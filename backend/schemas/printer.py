from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HotFolderCreate(BaseModel):
    """Schema for creating a hot folder mapping."""
    id: str  # e.g., "bottle_jig_v1"
    path: str  # e.g., "C:\EdgePrint\hotfolders\bottle_jig_v1\"
    description: Optional[str] = None


class HotFolderResponse(BaseModel):
    """Schema for hot folder in responses."""
    id: str
    path: str
    description: Optional[str]

    class Config:
        from_attributes = True


class PrinterCreate(BaseModel):
    """Schema for creating a new printer."""
    id: str  # e.g., "b1070uv-brooklyn"
    name: str  # e.g., "Epson B1070UV - Brooklyn"
    location: Optional[str] = None
    hot_folders: Optional[List[HotFolderCreate]] = []


class PrinterUpdate(BaseModel):
    """Schema for updating a printer."""
    name: Optional[str] = None
    location: Optional[str] = None
    is_online: Optional[bool] = None


class PrinterResponse(BaseModel):
    """Schema for printer in responses."""
    id: str
    name: str
    location: Optional[str]
    is_online: bool
    last_seen: Optional[datetime]
    hot_folders: List[HotFolderResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrinterHeartbeat(BaseModel):
    """Schema for printer agent heartbeat."""
    printer_id: str
    agent_version: Optional[str] = None



