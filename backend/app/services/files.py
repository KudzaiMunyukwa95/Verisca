import os
import shutil
import uuid
from fastapi import UploadFile
from pathlib import Path

class FileService:
    UPLOAD_DIR = Path("uploads")
    
    @staticmethod
    async def save_upload(file: UploadFile, subdirectory: str = "") -> dict:
        """
        Saves an uploaded file to the local filesystem.
        Returns metadata dict (path, stored_filename, size).
        """
        FileService.UPLOAD_DIR.mkdir(exist_ok=True)
        
        target_dir = FileService.UPLOAD_DIR
        if subdirectory:
            target_dir = target_dir / subdirectory
            target_dir.mkdir(exist_ok=True, parents=True)
            
        file_ext = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4()}{file_ext}"
        destination_path = target_dir / stored_filename
        
        # Save file
        with destination_path.open("wb") as buffer:
             shutil.copyfileobj(file.file, buffer)
             
        file_size = os.path.getsize(destination_path)
        
        # Construct a relative URL or Path
        # In production this would be an S3 key/url
        relative_path = str(destination_path)
        url = f"/static/{stored_filename}" 
        
        return {
            "filename": file.filename,
            "stored_filename": stored_filename,
            "file_path": relative_path,
            "content_type": file.content_type,
            "file_size": file_size,
            "url": url
        }
