from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.job import JobStatus


class JobSlotCreate(BaseModel):
    """Schema for creating a job slot."""
    template_slot_id: str  # e.g., "bottle_main"
    label_asset_path: Optional[str] = None
    guest_name: Optional[str] = None
    recipient: Optional[str] = None
    fragrance_id: Optional[str] = None
    fragrance_name: Optional[str] = None
    product_type: Optional[str] = None


class JobSlotResponse(BaseModel):
    """Schema for job slot in responses."""
    id: int
    template_slot_id: str
    slot_position: Optional[str]
    slot_label: Optional[str]
    label_asset_path: Optional[str]
    label_preview_path: Optional[str]
    guest_name: Optional[str]
    recipient: Optional[str]
    fragrance_id: Optional[str]
    fragrance_name: Optional[str]
    product_type: Optional[str]
    qr_uid: Optional[str]

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    printer_id: str
    template_id: str
    job_name: Optional[str] = None
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    copies: int = 1
    priority: int = 0
    designer_notes: Optional[str] = None
    slots: Optional[List[JobSlotCreate]] = []


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    job_name: Optional[str] = None
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    copies: Optional[int] = None
    priority: Optional[int] = None
    designer_notes: Optional[str] = None
    operator_notes: Optional[str] = None


class JobStatusUpdate(BaseModel):
    """Schema for updating job status."""
    status: JobStatus
    notes: Optional[str] = None  # Reason for status change
    reprint_reason: Optional[str] = None  # If failing/reprinting


class JobResponse(BaseModel):
    """Schema for job in responses."""
    id: int
    printer_id: str
    template_id: str
    status: JobStatus
    queue_position: Optional[int]
    local_queue_position: Optional[int]
    priority: int
    job_name: Optional[str]
    event_name: Optional[str]
    event_date: Optional[datetime]
    copies: int
    composed_pdf_path: Optional[str]
    created_by: Optional[int]
    reprint_of: Optional[int]
    reprint_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    downloaded_at: Optional[datetime]
    printed_at: Optional[datetime]
    operator_notes: Optional[str]
    designer_notes: Optional[str]
    slots: List[JobSlotResponse]

    class Config:
        from_attributes = True


class JobQueueItem(BaseModel):
    """Simplified job info for queue display."""
    id: int
    job_name: Optional[str]
    event_name: Optional[str]
    event_date: Optional[datetime]
    status: JobStatus
    queue_position: Optional[int]
    local_queue_position: Optional[int]
    priority: int
    copies: int
    template_id: str
    slot_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class JobReorderRequest(BaseModel):
    """Schema for reordering jobs in local queue."""
    job_ids: List[int]  # Jobs in desired order


class JobPrintRequest(BaseModel):
    """Schema for triggering print."""
    confirm: bool = True  # Operator confirms ready to print


