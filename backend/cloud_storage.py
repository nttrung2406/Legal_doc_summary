import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os 
from cloudinary.utils import cloudinary_url
import cloudinary.api
from cloudinary.exceptions import Error
load_dotenv()
# Configuration       
cloudinary.config( 
    cloud_name = os.getenv("CLOUD_NAME"), 
    api_key = os.getenv("CLOUD_API_KEY"),
    api_secret = os.getenv("CLOUD_API_SECRET"), 
    secure=True
)

# Upload file to Cloudinary 
def upload_file_to_cloud(file, public_id):
    try:
        upload_result = cloudinary.uploader.upload(file, resource_type="auto", public_id=public_id)
        return upload_result
    except Error as e:
        print("Upload failed:", e)
        return None  


# Get 1 (or many) file(s) from Cloudinary with public_id in the array document_ids 
def get_files(document_ids):
    if (not isinstance(document_ids, list) or len(document_ids) == 0):
        return False, "document_ids must be a non-empty array."
    options = { 'max_results': 50 }
    result = cloudinary.api.resources(**options)
    matched_files = [file for file in result['resources'] if file['public_id'] in document_ids]
    return True, matched_files 

# Delete file with public_id is document_id on Cloudinary 
def delete_file(document_id):
    if not document_id:
        return False, "Document ID is required."
    cloudinary.uploader.destroy(document_id)
    return True 
#print(delete_file("Report_1"))
