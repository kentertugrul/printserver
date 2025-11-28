"""
Supabase Storage Service

Handles file uploads and downloads for:
- Jig template PDFs
- Label artwork
- Composed print PDFs
"""

import os
from typing import Optional
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xujrxygkopokfpfbwjgt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1anJ4eWdrb3Bva2ZwZmJ3amd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyOTYxOTAsImV4cCI6MjA3OTg3MjE5MH0.qYJRh8RG_SGCYliqgWsxOtIJpurj77ZgflXZpgfPBHs")
BUCKET_NAME = "print-assets"

# Initialize Supabase client
_supabase: Optional[Client] = None

def get_supabase() -> Client:
    """Get or create Supabase client."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def upload_file(file_bytes: bytes, path: str, content_type: str = "application/pdf") -> str:
    """
    Upload a file to Supabase storage.
    
    Args:
        file_bytes: The file content as bytes
        path: The path in the bucket (e.g., "templates/jig_v1.pdf")
        content_type: MIME type of the file
    
    Returns:
        The public URL of the uploaded file
    """
    supabase = get_supabase()
    
    # Upload to storage
    result = supabase.storage.from_(BUCKET_NAME).upload(
        path,
        file_bytes,
        {"content-type": content_type}
    )
    
    # Get public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
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
    path = f"templates/{template_id}/{filename}"
    return upload_file(file_bytes, path, "application/pdf")


def upload_label_artwork(job_id: int, slot_id: str, file_bytes: bytes, filename: str) -> str:
    """
    Upload label artwork for a job slot.
    
    Args:
        job_id: The job ID
        slot_id: The slot ID
        file_bytes: Image file content
        filename: Original filename
    
    Returns:
        Public URL of the uploaded artwork
    """
    # Determine content type from filename
    ext = filename.lower().split('.')[-1]
    content_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    # Create path: jobs/{job_id}/slots/{slot_id}/{filename}
    path = f"jobs/{job_id}/slots/{slot_id}/{filename}"
    return upload_file(file_bytes, path, content_type)


def upload_composed_pdf(job_id: int, file_bytes: bytes) -> str:
    """
    Upload a composed print-ready PDF.
    
    Args:
        job_id: The job ID
        file_bytes: PDF file content
    
    Returns:
        Public URL of the uploaded PDF
    """
    path = f"jobs/{job_id}/composed.pdf"
    return upload_file(file_bytes, path, "application/pdf")


def delete_file(path: str) -> bool:
    """
    Delete a file from storage.
    
    Args:
        path: The path in the bucket
    
    Returns:
        True if successful
    """
    try:
        supabase = get_supabase()
        supabase.storage.from_(BUCKET_NAME).remove([path])
        return True
    except Exception as e:
        print(f"Error deleting file {path}: {e}")
        return False


def get_public_url(path: str) -> str:
    """
    Get the public URL for a file.
    
    Args:
        path: The path in the bucket
    
    Returns:
        Public URL
    """
    supabase = get_supabase()
    return supabase.storage.from_(BUCKET_NAME).get_public_url(path)

