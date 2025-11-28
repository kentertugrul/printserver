from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models import get_db, Template, TemplateSlot, User, UserRole
from schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate, TemplateSlotCreate
from api.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    active_only: bool = True,
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(get_current_user)
):
    """List all templates."""
    query = db.query(Template)
    if active_only:
        query = query.filter(Template.is_active == True)
    return query.all()


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Create a new template (admin only)."""
    # Check if ID exists
    existing = db.query(Template).filter(Template.id == template_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template ID already exists")
    
    template = Template(
        id=template_data.id,
        name=template_data.name,
        description=template_data.description,
        bed_width=template_data.bed_width,
        bed_height=template_data.bed_height,
        hot_folder_type=template_data.hot_folder_type,
    )
    db.add(template)
    
    # Add slots
    for slot_data in template_data.slots or []:
        slot = TemplateSlot(
            id=slot_data.id,
            template_id=template_data.id,
            name=slot_data.name,
            slot_position=slot_data.slot_position,
            x=slot_data.x,
            y=slot_data.y,
            width=slot_data.width,
            height=slot_data.height,
            rotation=slot_data.rotation,
            product_type=slot_data.product_type,
            display_order=slot_data.display_order,
        )
        db.add(slot)
    
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(get_current_user)
):
    """Get a specific template."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update a template (admin only)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template_data.name is not None:
        template.name = template_data.name
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.is_active is not None:
        template.is_active = template_data.is_active
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Delete a template (admin only)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


@router.post("/{template_id}/slots", response_model=TemplateResponse)
async def add_template_slot(
    template_id: str,
    slot_data: TemplateSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Add a slot to a template (admin only)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if slot ID exists for this template
    existing = db.query(TemplateSlot).filter(
        TemplateSlot.id == slot_data.id,
        TemplateSlot.template_id == template_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slot ID already exists for this template")
    
    slot = TemplateSlot(
        id=slot_data.id,
        template_id=template_id,
        name=slot_data.name,
        slot_position=slot_data.slot_position,
        x=slot_data.x,
        y=slot_data.y,
        width=slot_data.width,
        height=slot_data.height,
        rotation=slot_data.rotation,
        product_type=slot_data.product_type,
        display_order=slot_data.display_order,
    )
    db.add(slot)
    db.commit()
    db.refresh(template)
    return template


