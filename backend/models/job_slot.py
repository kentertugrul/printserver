from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class JobSlot(Base):
    """
    Represents one slot in a print job's jig layout.
    
    For example, if a jig has 4 positions (30ml bottle, 2x 5ml minis, 1x box top),
    a job would have 4 JobSlot records, each describing what label goes where.
    
    This powers the operator's jig map display:
        Slot A – Box top – "Sarah"
        Slot B – 30ml – "Sarah"  
        Slot C – 5ml – "Sarah – Mini 1"
        Slot D – 5ml – "Sarah – Mini 2"
    """
    __tablename__ = "job_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Which template slot this fills
    template_slot_id = Column(String(50), nullable=False)  # e.g., "bottle_main", "mini_1", "box_top"
    
    # Position in the jig (for operator display)
    slot_position = Column(String(10))  # e.g., "A", "B", "C", "D"
    slot_label = Column(String(100))  # Human-readable: "30ml Bottle", "Mini 1", "Box Top"
    
    # Label asset
    label_asset_path = Column(Text)  # Path to the uploaded label image/PDF
    label_preview_path = Column(Text)  # Path to thumbnail for preview
    
    # What this label represents
    guest_name = Column(String(200))  # e.g., "Sarah"
    recipient = Column(String(200))  # If different from guest (e.g., for favors)
    
    # Product info
    fragrance_id = Column(String(50))  # SKU or internal fragrance code
    fragrance_name = Column(String(200))  # e.g., "Midnight Rose"
    product_type = Column(String(50))  # e.g., "30ml_bottle", "5ml_mini", "box_top"
    
    # Optional QC tracking
    qr_uid = Column(String(100))  # Unique ID for QR code on label (for scanning verification)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="slots")



