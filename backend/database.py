from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.legal_doc_db

# Collections
users_collection = db.users
documents_collection = db.documents
api_usage_collection = db.api_usage

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") 
MAX_REQUESTS_PER_DAY = os.getenv("MAX_REQUESTS_PER_DAY") 
REQUEST_COOLDOWN = os.getenv("REQUEST_COOLDOWN")  

def check_api_usage(user_id: str) -> tuple[bool, str]:
    """Check if user has exceeded daily API limit or needs to wait for cooldown."""
    today = datetime.now().date()
    
    usage = api_usage_collection.find_one({
        "user_id": user_id,
        "date": today
    })
    
    if not usage:
        api_usage_collection.insert_one({
            "user_id": user_id,
            "date": today,
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
            "date": today
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

def save_document(user_id: str, filename: str, chunks: list, embeddings: list):
    document = {
        "user_id": user_id,
        "filename": filename,
        "chunks": chunks,
        "embeddings": embeddings,
        "created_at": datetime.utcnow()
    }
    documents_collection.insert_one(document)
    return True, "Document saved successfully"

def get_user_documents(user_id: str):
    return list(documents_collection.find({"user_id": user_id}))

def get_document_by_filename(filename: str):
    return documents_collection.find_one({"filename": filename}) 