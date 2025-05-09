from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Request, Form, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, Response
from datetime import timedelta
import shutil
import time
import os
from typing import List, Optional
from jose import jwt, JWTError
from pydantic import BaseModel
import logging
from fastapi.responses import StreamingResponse
import httpx
from io import BytesIO
import threading
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette_prometheus import metrics, PrometheusMiddleware
from gemini_integration import gemini_service
from gemini_metrics import GeminiMetrics

from database import (
    create_user, verify_user, create_access_token,
    save_document, get_user_documents, get_document_by_filename, get_document_by_id, delete_pdf_file,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    users_collection, documents_collection
)
from document_processor import (
    extract_text_from_pdf, chunk_text, generate_embeddings, generate_summary, extract_clauses, generate_chat_response,
    get_similar_chunks
)
from cloud_storage import (upload_file_to_cloud, get_file, delete_file, get_pdf_url)
from monitoring import (
    monitor_request, update_system_metrics,
    UPLOAD_COUNT, CHAT_REQUESTS, SUMMARY_REQUESTS
)

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add basic auth security
security = HTTPBasic()

def verify_metrics_auth(credentials: HTTPBasicCredentials = Security(security)):
    correct_username = "admin"
    correct_password = "admin"
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

# Add request monitoring middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    return await monitor_request(request, call_next)

# Start system metrics update thread
metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class ChatRequest(BaseModel):
    query: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = users_collection.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/signup")
async def signup(request: SignupRequest):
    success, message = create_user(request.username, request.email, request.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    success, result = verify_user(form_data.username, form_data.password)
    if not success:
        raise HTTPException(status_code=401, detail=result)
    
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_name = os.path.splitext(file.filename)[0]
    current_user_id = str(current_user["_id"])
    file_path = os.path.join(UPLOAD_DIR, file_name)
    public_id = None
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file.file.seek(0)
        
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        embeddings = generate_embeddings(chunks)

        public_id = current_user_id + "_" + file_name
        logger.debug(f"Uploading to Cloudinary with public_id: {public_id}")
        
        # Upload to Cloudinary
        upload_result = upload_file_to_cloud(file.file, public_id)
        if not upload_result:
            raise HTTPException(status_code=500, detail="Failed to upload file to cloud storage")
        result1, clause_list = extract_clauses(text, str(current_user["_id"]))
        time.sleep(10)
        result2, summary = generate_summary(text, str(current_user["_id"])) 
        print(summary)
        logger.debug(clause_list)
        # Save document to database
        success = None
        message = None
        if result1 and result2:
            success, message = save_document(
                current_user["_id"],
                file.filename,
                summary,
                clause_list,
                chunks,
                embeddings,
                file.file  # Pass the file object for GridFS
            )
        
        if not success:
            if (public_id):
                delete_file(public_id)
            raise HTTPException(status_code=500, detail=message)
        
        UPLOAD_COUNT.labels(status="success").inc()
        return {"message": "File processed successfully"}
    
    except Exception as e:
        UPLOAD_COUNT.labels(status="error").inc()
        logger.error(f"Error in upload endpoint: {str(e)}", exc_info=True)
        if (public_id):
                delete_file(public_id)
        # Clean up temporary file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    documents = get_user_documents(current_user["_id"])
    return [{"id": str(doc["_id"]),"filename": doc["filename"], "created_at": doc["created_at"]} for doc in documents]

@app.get("/document/{filename}/{documentId}")
async def get_document(filename: str, documentId: str, current_user: dict = Depends(get_current_user)):
    # document = get_document_by_filename(filename)
    # if not document or str(document["user_id"]) != str(current_user["_id"]):
    #     raise HTTPException(status_code=404, detail="Document not found")
    
    # document["_id"] = str(document["_id"])
    # document["user_id"] = str(document["user_id"])
    # return document
    file_name = os.path.splitext(filename)[0]
    current_user_id = str(current_user["_id"])
    public_id = current_user_id + "_" + file_name
    file = get_file(public_id)
    logger.debug(file)
    try:
        pdf_url =  get_pdf_url(public_id)
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="File not found")
        return StreamingResponse(
            BytesIO(response.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        logger.debug(e)

@app.post("/summarize/{filename}/{documentId}")
async def summarize_document(
    filename: str,
    documentId: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_id(documentId)
    
    if not document or document["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    SUMMARY_REQUESTS.labels(status="success").inc()
    return {"summary": document['summary']}

@app.get("/clauses/{filename}/{documentId}")
async def get_paragraph_summaries(
    filename: str,
    documentId: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_id(documentId)
    if not document or document["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"clauses" :document['clauses']}

@app.post("/chat/{filename}/{documentId}")
async def chat_with_document(
    filename: str,
    documentId: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_id(documentId)
    if not document or str(document["user_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Document not found")
    
    similar_chunks = get_similar_chunks(request.query, document["chunks"], document["embeddings"])
    success, result = generate_chat_response(request.query, similar_chunks, str(current_user["_id"]))
    if not success:
        raise HTTPException(status_code=429, detail=result)
    CHAT_REQUESTS.labels(status="success").inc()
    return {"response": result}

@app.get("/serve-pdf/{filename}")
async def serve_pdf(filename: str, current_user: dict = Depends(get_current_user)):
    document = get_document_by_filename(filename)
    if not document or document["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        return FileResponse(
            file_path,
            media_type="application/pdf",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {str(e)}")

# Add Gemini endpoints
@app.post("/api/summarize")
async def summarize_text(text: str = Form(...), reference: Optional[str] = Form(None)):
    try:
        result = await gemini_service.generate_summary(text, reference)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    try:
        result = await gemini_service.chat(message)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gemini/metrics/recent")
async def get_recent_metrics(limit: int = 100):
    """Get recent Gemini API metrics."""
    try:
        metrics = GeminiMetrics.get_recent_metrics(limit)
        return JSONResponse(content=metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gemini/metrics/summary")
async def get_metrics_summary():
    """Get summary statistics of Gemini API metrics."""
    try:
        summary = GeminiMetrics.get_metrics_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/authorize")
async def oauth_authorize():
    """OAuth authorization endpoint."""
    return {"message": "Authorization endpoint"}

@app.post("/oauth/token")
async def oauth_token():
    """OAuth token endpoint."""
    return {"message": "Token endpoint"}

@app.get("/oauth/userinfo")
async def oauth_userinfo(current_user: dict = Depends(get_current_user)):
    """OAuth user info endpoint."""
    return {
        "sub": str(current_user["_id"]),
        "name": current_user["username"],
        "email": current_user["email"],
        "preferred_username": current_user["username"]
    }

@app.get("/metrics/gemini")
async def gemini_metrics(credentials: HTTPBasicCredentials = Security(security)):
    """Expose Gemini metrics to Prometheus with basic authentication."""
    if credentials.username != "admin" or credentials.password != "admin":
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.delete("/delete/{filename}/{documentId}")
async def delete_document(
    filename: str,
    documentId: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_id(documentId)
    result = delete_pdf_file(documentId)
    if result:
        publicId = str(current_user["_id"]) + "_" + os.path.splitext(filename)[0]
        print(publicId)
        result = delete_file(publicId)
        return {"response": result}
    else:
        result = documents_collection.insert_one(document)
        return {"response": (False, "An error occured")}