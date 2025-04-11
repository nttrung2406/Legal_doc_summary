from pymongo import MongoClient
from gridfs import GridFS
from passlib.context import CryptContext
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from typing import Optional
import os
from dotenv import load_dotenv
from bson import ObjectId
import json
import logging

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.legal_doc_db

# Collections
users_collection = db.users
documents_collection = db.documents
api_usage_collection = db.api_usage

# GridFS
fs = GridFS(db)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") 
MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY", "10"))
REQUEST_COOLDOWN = float(os.getenv("REQUEST_COOLDOWN", "1.0"))

def check_api_usage(user_id: str) -> tuple[bool, str]:
    """Check if user has exceeded daily API limit or needs to wait for cooldown."""
    today = datetime.now().date()
    
    usage = api_usage_collection.find_one({
        "user_id": user_id,
        "date": today.isoformat()  # Convert date to ISO format string
    })
    
    if not usage:
        api_usage_collection.insert_one({
            "user_id": user_id,
            "date": today.isoformat(),  # Convert date to ISO format string
            "request_count": 0,
            "last_request_time": None
        })
        return True, ""
    
    if usage["request_count"] >= MAX_REQUESTS_PER_DAY:
        return False, "Daily API limit reached. Please try again tomorrow."
    
    if usage["last_request_time"]:
        time_since_last_request = (datetime.utcnow() - usage["last_request_time"]).total_seconds()
        if time_since_last_request < REQUEST_COOLDOWN:
            wait_time = REQUEST_COOLDOWN - time_since_last_request
            return False, f"Please wait {wait_time:.1f} seconds before making another request."
    
    return True, ""

def update_api_usage(user_id: str):
    """Update API usage count and last request time."""
    today = datetime.now().date()
    
    api_usage_collection.update_one(
        {
            "user_id": user_id,
            "date": today.isoformat()  # Convert date to ISO format string
        },
        {
            "$inc": {"request_count": 1},
            "$set": {"last_request_time": datetime.utcnow()}
        }
    )

def create_user(username: str, email: str, password: str):
    if users_collection.find_one({"username": username}):
        return False, "Username already exists"
    
    hashed_password = pwd_context.hash(password)
    user = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.now()
    }
    users_collection.insert_one(user)
    return True, "User created successfully"

def verify_user(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user:
        print(f"User not found: {username}")
        return False, "User not found"
    
    print(f"Verifying password for user: {username}")
    print(f"Stored hashed password: {user['hashed_password']}")
    
    if not pwd_context.verify(password, user["hashed_password"]):
        print("Password verification failed")
        return False, "Incorrect password"
    
    print("Password verification succeeded")
    return True, user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def save_document(user_id: str, filename: str, chunks: list, embeddings: list, pdf_file):
    try:
        # Save PDF to GridFS
        pdf_id = fs.put(pdf_file, filename=filename)
        
        document = {
            "user_id": user_id,
            "filename": filename,
            "chunks": chunks,
            "embeddings": embeddings,
            "pdf_id": str(pdf_id),  # Convert ObjectId to string
            "created_at": datetime.now()
        }
        
        result = documents_collection.insert_one(document)
        return True, "Document saved successfully"
    except Exception as e:
        logger.error(f"Error saving document: {str(e)}", exc_info=True)
        return False, f"Error saving document: {str(e)}"

def get_user_documents(user_id: str):
    documents = documents_collection.find({"user_id": user_id})
    return [
        {
            "_id": str(doc["_id"]),  # Convert ObjectId to string
            "filename": doc["filename"],
            "created_at": doc["created_at"].isoformat() if isinstance(doc["created_at"], (datetime, date)) else doc["created_at"],
            "user_id": str(doc["user_id"])  # Convert ObjectId to string
        }
        for doc in documents
    ]

def get_document_by_filename(filename: str):
    print(f"Looking for document with filename: {filename}")
    document = documents_collection.find_one({"filename": filename})

    if not document:
        print("No document found")
        return None
    
    print(f"Found document!!!!")
    # Convert ObjectId to string and datetime to ISO format
    document['_id'] = str(document['_id'])
    document['user_id'] = str(document['user_id'])
    if 'created_at' in document:
        document['created_at'] = document['created_at'].isoformat() if isinstance(document['created_at'], (datetime, date)) else document['created_at']
    return document

def get_pdf_file(pdf_id):
    """Retrieve PDF file from GridFS"""
    try:
        return fs.get(ObjectId(pdf_id))
    except:
        return None
