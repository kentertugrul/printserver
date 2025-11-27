from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Template(Base):
    """
    Defines a jig layout template.
    
    Each template describes the physical layout of a jig:
    - What slots are available
    - Where each slot is positioned on the print bed
    - The dimensions and rotation of each slot
    
    Example: "30ml + 2×5ml + box top" template
    """
    __tablename__ = "templates"

    id = Column(String(50), primary_key=True)  # e.g., "bottle_jig_v1"
    name = Column(String(100), nullable=False)  # e.g., "30ml Bottle + 2x Mini + Box"
    description = Column(Text)
    
    # Physical bed dimensions (in mm)
    bed_width = Column(Float, nullable=False)  # e.g., 329 (A3+ width)
    bed_height = Column(Float, nullable=False)  # e.g., 483 (A3+ height)
    
    # Which hot folder type this template uses
    hot_folder_type = Column(String(50), nullable=False)  # e.g., "bottle_jig_v1"
    
    # Template PDF for composition (jig layout PDF uploaded by user)
    template_pdf_path = Column(Text)  # Path to the jig template PDF
    
    # Preview image (auto-generated from PDF or uploaded)
    template_preview_path = Column(Text)  # Path to preview image of template
    
    # Preview image for designers
    preview_image_path = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    slots = relationship("TemplateSlot", back_populates="template", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="template")


class TemplateSlot(Base):
    """
    Defines a single slot position within a template.
    
    Each slot has:
    - Physical position (x, y in mm from top-left)
    - Dimensions (width, height in mm)
    - Rotation (for cylindrical surfaces)
    - Type (what kind of product fits here)
    """
    __tablename__ = "template_slots"

    id = Column(String(50), primary_key=True)  # e.g., "bottle_main"
    template_id = Column(String(50), ForeignKey("templates.id"), primary_key=True)
    
    # Human-readable info
    name = Column(String(100), nullable=False)  # e.g., "30ml Main Bottle"
    slot_position = Column(String(10))  # Letter for operator: "A", "B", "C"
    
    # Position on bed (mm from top-left)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    
    # Printable area dimensions (mm)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Rotation (degrees, for cylindrical labels)
    rotation = Column(Float, default=0)
    
    # What product type this slot accepts
    product_type = Column(String(50))  # e.g., "30ml_bottle", "5ml_mini", "box_top"
    
    # Order for display
    display_order = Column(Integer, default=0)
    
    # Relationship
    template = relationship("Template", back_populates="slots")

