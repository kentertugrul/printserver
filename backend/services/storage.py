"""
Supabase Storage Service

Handles file uploads and downloads using direct HTTP requests.
"""

import os
import httpx
from typing import Optional

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xujrxygkopokfpfbwjgt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1anJ4eWdrb3Bva2ZwZmJ3amd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyOTYxOTAsImV4cCI6MjA3OTg3MjE5MH0.qYJRh8RG_SGCYliqgWsxOtIJpurj77ZgflXZpgfPBHs")
BUCKET_NAME = "print-assets"


def upload_file(file_bytes: bytes, path: str, content_type: str = "application/pdf") -> str:
    """
    Upload a file to Supabase storage using direct HTTP.
    
    Args:
        file_bytes: The file content as bytes
        path: The path in the bucket (e.g., "templates/jig_v1.pdf")
        content_type: MIME type of the file
    
    Returns:
        The public URL of the uploaded file
    """
    # Supabase storage API URL
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
    }
    
    # Upload the file
    response = httpx.post(upload_url, content=file_bytes, headers=headers, timeout=30.0)
    
    if response.status_code == 200:
        # File uploaded successfully
        pass
    elif response.status_code == 400 and "already exists" in response.text.lower():
        # File already exists, try to update it
        response = httpx.put(upload_url, content=file_bytes, headers=headers, timeout=30.0)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to update file: {response.text}")
    elif response.status_code not in [200, 201]:
        raise Exception(f"Failed to upload file: {response.text}")
    
    # Return public URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
    return public_url


def upload_template_pdf(template_id: str, file_bytes: bytes, filename: str) -> str:
    """
    Upload a template jig PDF.
    
    Args:
        template_id: The template ID
        file_bytes: PDF file content
        filename: Original filename
    
    Returns:
        Public URL of the uploaded PDF
    """
    # Create path: templates/{template_id}/{filename}
    # Sanitize filename
    safe_filename = filename.replace(" ", "_").replace("(", "").replace(")", "")
    path = f"templates/{template_id}/{safe_filename}"
    return upload_file(file_bytes, path, "application/pdf")


def upload_label_artwork(job_id: int, slot_id: str, file_bytes: bytes, filename: str) -> str:
    """
    Upload label artwork for a job slot.
    """
    ext = filename.lower().split('.')[-1]
    content_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    safe_filename = filename.replace(" ", "_")
    path = f"jobs/{job_id}/slots/{slot_id}/{safe_filename}"
    return upload_file(file_bytes, path, content_type)


def upload_composed_pdf(job_id: int, file_bytes: bytes) -> str:
    """
    Upload a composed print-ready PDF.
    """
    path = f"jobs/{job_id}/composed.pdf"
    return upload_file(file_bytes, path, "application/pdf")


def delete_file(path: str) -> bool:
    """
    Delete a file from storage.
    """
    try:
        delete_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
        }
        response = httpx.delete(delete_url, headers=headers, timeout=30.0)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error deleting file {path}: {e}")
        return False


def get_public_url(path: str) -> str:
    """
    Get the public URL for a file.
    """
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
