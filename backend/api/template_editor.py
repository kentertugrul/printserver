"""
Template Editor API endpoints.

Supports:
1. Uploading jig PDF templates (to Supabase storage)
2. Visual slot definition (saving coordinates from the editor UI)
3. Generating preview images from PDFs
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json

from models import get_db, Template, TemplateSlot, User, UserRole
from schemas.template import TemplateResponse, TemplateSlotCreate
from api.auth import get_current_user, require_role

router = APIRouter()


# Import storage service
try:
    from services.storage import upload_template_pdf as supabase_upload_template_pdf
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Warning: Supabase storage not available")


@router.post("/{template_id}/upload-jig", response_model=TemplateResponse)
async def upload_template_jig_pdf(
    template_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Upload a jig PDF template to Supabase storage.
    
    This PDF will be used as the base layer for composing print files.
    Labels will be overlaid onto this PDF at the defined slot positions.
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content
    content = await file.read()
    
    if HAS_SUPABASE:
        # Upload to Supabase
        try:
            public_url = supabase_upload_template_pdf(template_id, content, file.filename)
            template.template_pdf_path = public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")
    else:
        # Fallback to local storage
        template_dir = f"./templates/{template_id}"
        os.makedirs(template_dir, exist_ok=True)
        pdf_path = f"{template_dir}/template.pdf"
        with open(pdf_path, "wb") as f:
            f.write(content)
        template.template_pdf_path = pdf_path
    
    db.commit()
    db.refresh(template)
    
    return template


@router.post("/{template_id}/slots/visual", response_model=TemplateResponse)
async def save_visual_slots(
    template_id: str,
    slots_json: str = Form(...),
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Save slot definitions from the visual editor.
    
    Expects a JSON array of slots with x, y, width, height (as percentages of the template),
    which will be converted to mm based on the template's bed dimensions.
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        slots_data = json.loads(slots_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Delete existing slots
    db.query(TemplateSlot).filter(TemplateSlot.template_id == template_id).delete()
    
    # Create new slots, converting percentages to mm
    for i, slot_data in enumerate(slots_data):
        # Convert percentages to mm
        x_mm = (slot_data["x_percent"] / 100) * template.bed_width
        y_mm = (slot_data["y_percent"] / 100) * template.bed_height
        width_mm = (slot_data["width_percent"] / 100) * template.bed_width
        height_mm = (slot_data["height_percent"] / 100) * template.bed_height
        
        slot = TemplateSlot(
            id=slot_data.get("id", f"slot_{i+1}"),
            template_id=template_id,
            name=slot_data.get("name", f"Slot {i+1}"),
            slot_position=slot_data.get("slot_position", chr(65 + i)),  # A, B, C...
            x=x_mm,
            y=y_mm,
            width=width_mm,
            height=height_mm,
            rotation=slot_data.get("rotation", 0),
            product_type=slot_data.get("product_type"),
            display_order=i,
        )
        db.add(slot)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/{template_id}/slots/visual")
async def get_visual_slots(
    template_id: str,
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(get_current_user)
):
    """
    Get slot definitions in percentage format for the visual editor.
    
    Returns slots with x, y, width, height as percentages of the template dimensions.
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    slots_visual = []
    for slot in template.slots:
        slots_visual.append({
            "id": slot.id,
            "name": slot.name,
            "slot_position": slot.slot_position,
            "x_percent": (slot.x / template.bed_width) * 100,
            "y_percent": (slot.y / template.bed_height) * 100,
            "width_percent": (slot.width / template.bed_width) * 100,
            "height_percent": (slot.height / template.bed_height) * 100,
            "rotation": slot.rotation,
            "product_type": slot.product_type,
            "display_order": slot.display_order,
        })
    
    return {
        "template_id": template_id,
        "bed_width_mm": template.bed_width,
        "bed_height_mm": template.bed_height,
        "has_pdf": bool(template.template_pdf_path),
        "pdf_url": template.template_pdf_path,
        "slots": sorted(slots_visual, key=lambda s: s["display_order"]),
    }
