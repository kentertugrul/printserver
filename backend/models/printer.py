from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Printer(Base):
    """
    Represents a physical printer (e.g., Epson B1070UV).
    Each printer can have multiple hot folders for different jig types.
    """
    __tablename__ = "printers"

    id = Column(String(50), primary_key=True)  # e.g., "b1070uv-brooklyn"
    name = Column(String(100), nullable=False)  # e.g., "Epson B1070UV - Brooklyn"
    location = Column(String(100))  # e.g., "Brooklyn Studio"
    
    # API key for the print agent running on this printer's PC
    api_key = Column(String(64), unique=True, nullable=False)
    
    # Status tracking
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    
    # Relationships
    hot_folders = relationship("HotFolder", back_populates="printer", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="printer")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HotFolder(Base):
    """
    Maps jig/template types to EdgePrint hot folder paths.
    E.g., bottle_jig_v1 -> C:\EdgePrint\hotfolders\bottle_jig_v1\
    """
    __tablename__ = "hot_folders"

    id = Column(String(50), primary_key=True)  # e.g., "bottle_jig_v1"
    printer_id = Column(String(50), ForeignKey("printers.id"), primary_key=True)
    
    path = Column(Text, nullable=False)  # e.g., "C:\EdgePrint\hotfolders\bottle_jig_v1\"
    description = Column(String(200))  # e.g., "30ml bottle + 2x5ml + box top"
    
    printer = relationship("Printer", back_populates="hot_folders")



