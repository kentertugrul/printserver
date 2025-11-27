from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TemplateSlotCreate(BaseModel):
    """Schema for creating a template slot."""
    id: str  # e.g., "bottle_main"
    name: str  # e.g., "30ml Main Bottle"
    slot_position: Optional[str] = None  # e.g., "A"
    x: float  # Position in mm
    y: float
    width: float  # Dimensions in mm
    height: float
    rotation: float = 0
    product_type: Optional[str] = None  # e.g., "30ml_bottle"
    display_order: int = 0


class TemplateSlotResponse(BaseModel):
    """Schema for template slot in responses."""
    id: str
    name: str
    slot_position: Optional[str]
    x: float
    y: float
    width: float
    height: float
    rotation: float
    product_type: Optional[str]
    display_order: int

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    """Schema for creating a template."""
    id: str  # e.g., "bottle_jig_v1"
    name: str  # e.g., "30ml Bottle + 2x Mini + Box"
    description: Optional[str] = None
    bed_width: float  # mm
    bed_height: float  # mm
    hot_folder_type: str  # Which hot folder to use
    slots: Optional[List[TemplateSlotCreate]] = []


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Schema for template in responses."""
    id: str
    name: str
    description: Optional[str]
    bed_width: float
    bed_height: float
    hot_folder_type: str
    template_pdf_path: Optional[str]
    template_preview_path: Optional[str]
    preview_image_path: Optional[str]
    is_active: bool
    slots: List[TemplateSlotResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

