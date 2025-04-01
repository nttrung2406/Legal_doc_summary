from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import shutil
import os
from typing import List
import json
from jose import jwt, JWTError
from database import (
    create_user, verify_user, create_access_token,
    save_document, get_user_documents, get_document_by_filename,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    users_collection
)
from document_processor import (
    extract_text_from_pdf, chunk_text, generate_embeddings,
    generate_summary, generate_paragraph_summaries, generate_chat_response,
    get_similar_chunks
)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
async def signup(username: str, email: str, password: str):
    success, message = create_user(username, email, password)
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
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        embeddings = generate_embeddings(chunks)
        
        success, message = save_document(
            current_user["_id"],
            file.filename,
            chunks,
            embeddings
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {"message": "File processed successfully"}
    
    finally:
        os.remove(file_path)

@app.get("/documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    documents = get_user_documents(current_user["_id"])
    return [{"filename": doc["filename"], "created_at": doc["created_at"]} for doc in documents]

@app.get("/document/{filename}")
async def get_document(filename: str, current_user: dict = Depends(get_current_user)):
    document = get_document_by_filename(filename)
    if not document or document["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.post("/summarize/{filename}")
async def summarize_document(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_filename(filename)
    if not document or document["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    
    full_text = " ".join(document["chunks"])
    success, result = generate_summary(full_text, current_user["_id"])
    if not success:
        raise HTTPException(status_code=429, detail=result)
    return {"summary": result}

@app.get("/paragraph-summaries/{filename}")
async def get_paragraph_summaries(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_filename(filename)
    if not document or document["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    
    success, summaries, message = generate_paragraph_summaries(document["chunks"], current_user["_id"])
    if not success:
        raise HTTPException(status_code=429, detail=message)
    return {"summaries": summaries}

@app.post("/chat/{filename}")
async def chat_with_document(
    filename: str,
    query: str,
    current_user: dict = Depends(get_current_user)
):
    document = get_document_by_filename(filename)
    if not document or document["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    
    similar_chunks = get_similar_chunks(query, document["chunks"], document["embeddings"])
    success, result = generate_chat_response(query, similar_chunks, current_user["_id"])
    if not success:
        raise HTTPException(status_code=429, detail=result)
    return {"response": result} 