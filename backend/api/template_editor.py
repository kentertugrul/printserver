"""
Template Editor API endpoints.

Supports:
1. Uploading jig PDF templates
2. Visual slot definition (saving coordinates from the editor UI)
3. Generating preview images from PDFs
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
import aiofiles
from PIL import Image
from io import BytesIO

from models import get_db, Template, TemplateSlot, User, UserRole
from schemas.template import TemplateResponse, TemplateSlotCreate
from api.auth import get_current_user, require_role

router = APIRouter()

# Upload directories
TEMPLATE_DIR = os.getenv("TEMPLATE_DIR", "./templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Try to import pdf2image for PDF preview generation
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


@router.post("/{template_id}/upload-pdf", response_model=TemplateResponse)
async def upload_template_pdf(
    template_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Upload a jig PDF template.
    
    This PDF will be used as the base layer for composing print files.
    Labels will be overlaid onto this PDF at the defined slot positions.
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save the PDF
    template_dir = os.path.join(TEMPLATE_DIR, template_id)
    os.makedirs(template_dir, exist_ok=True)
    
    pdf_path = os.path.join(template_dir, "template.pdf")
    
    async with aiofiles.open(pdf_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    template.template_pdf_path = pdf_path
    
    # Generate preview image if possible
    preview_path = await _generate_pdf_preview(pdf_path, template_dir)
    if preview_path:
        template.template_preview_path = preview_path
    
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/{template_id}/pdf")
async def get_template_pdf(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the template PDF."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if not template.template_pdf_path or not os.path.exists(template.template_pdf_path):
        raise HTTPException(status_code=404, detail="Template PDF not found")
    
    return FileResponse(
        template.template_pdf_path,
        media_type="application/pdf",
        filename=f"{template_id}_template.pdf"
    )


@router.get("/{template_id}/preview")
async def get_template_preview(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the template preview image (PNG)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    preview_path = template.template_preview_path or template.preview_image_path
    
    if not preview_path or not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Preview not found")
    
    return FileResponse(
        preview_path,
        media_type="image/png",
        filename=f"{template_id}_preview.png"
    )


@router.post("/{template_id}/slots/visual", response_model=TemplateResponse)
async def save_visual_slots(
    template_id: str,
    slots_json: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Save slot definitions from the visual editor.
    
    Expects a JSON array of slots with x, y, width, height (as percentages of the template),
    which will be converted to mm based on the template's bed dimensions.
    
    JSON format:
    [
        {
            "id": "slot_a",
            "name": "30ml Bottle",
            "slot_position": "A",
            "x_percent": 10.5,
            "y_percent": 8.2,
            "width_percent": 25.0,
            "height_percent": 30.0,
            "rotation": 0,
            "product_type": "30ml_bottle"
        },
        ...
    ]
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
    current_user: User = Depends(get_current_user)
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
        "slots": sorted(slots_visual, key=lambda s: s["display_order"]),
    }


async def _generate_pdf_preview(pdf_path: str, output_dir: str) -> Optional[str]:
    """Generate a PNG preview from a PDF."""
    if not HAS_PDF2IMAGE:
        return None
    
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        if images:
            preview_path = os.path.join(output_dir, "preview.png")
            images[0].save(preview_path, "PNG")
            return preview_path
    except Exception as e:
        print(f"Warning: Could not generate PDF preview: {e}")
    
    return None


