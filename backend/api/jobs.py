from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os
import aiofiles

from models import get_db, Job, JobSlot, JobStatus, Printer, Template, User, UserRole
from schemas.job import (
    JobCreate, JobResponse, JobUpdate, JobStatusUpdate, 
    JobSlotCreate, JobSlotResponse
)
from api.auth import get_current_user, require_role

router = APIRouter()

# Upload directory for label assets
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    printer_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List jobs with optional filters."""
    query = db.query(Job)
    
    if printer_id:
        query = query.filter(Job.printer_id == printer_id)
    if status:
        query = query.filter(Job.status == status)
    
    # Order by priority (desc), then queue position, then created_at
    query = query.order_by(Job.priority.desc(), Job.queue_position, Job.created_at)
    
    return query.offset(offset).limit(limit).all()


@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new print job."""
    # Verify printer exists
    printer = db.query(Printer).filter(Printer.id == job_data.printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    # Verify template exists
    template = db.query(Template).filter(Template.id == job_data.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get next queue position
    max_pos = db.query(func.max(Job.queue_position)).filter(
        Job.printer_id == job_data.printer_id
    ).scalar() or 0
    
    job = Job(
        printer_id=job_data.printer_id,
        template_id=job_data.template_id,
        job_name=job_data.job_name,
        event_name=job_data.event_name,
        event_date=job_data.event_date,
        copies=job_data.copies,
        priority=job_data.priority,
        designer_notes=job_data.designer_notes,
        created_by=current_user.id,
        queue_position=max_pos + 1,
        status=JobStatus.DRAFT,
    )
    db.add(job)
    db.flush()  # Get the job ID
    
    # Add slots
    for slot_data in job_data.slots or []:
        # Find the template slot to get position info
        template_slot = next(
            (s for s in template.slots if s.id == slot_data.template_slot_id),
            None
        )
        slot = JobSlot(
            job_id=job.id,
            template_slot_id=slot_data.template_slot_id,
            slot_position=template_slot.slot_position if template_slot else None,
            slot_label=template_slot.name if template_slot else None,
            label_asset_path=slot_data.label_asset_path,
            guest_name=slot_data.guest_name,
            recipient=slot_data.recipient,
            fragrance_id=slot_data.fragrance_id,
            fragrance_name=slot_data.fragrance_name,
            product_type=slot_data.product_type or (template_slot.product_type if template_slot else None),
        )
        db.add(slot)
    
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job (only while in DRAFT or PENDING_REVIEW status)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Only allow editing in early stages
    if job.status not in [JobStatus.DRAFT, JobStatus.PENDING_REVIEW]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot edit job in {job.status.value} status"
        )
    
    if job_data.job_name is not None:
        job.job_name = job_data.job_name
    if job_data.event_name is not None:
        job.event_name = job_data.event_name
    if job_data.event_date is not None:
        job.event_date = job_data.event_date
    if job_data.copies is not None:
        job.copies = job_data.copies
    if job_data.priority is not None:
        job.priority = job_data.priority
    if job_data.designer_notes is not None:
        job.designer_notes = job_data.designer_notes
    if job_data.operator_notes is not None:
        job.operator_notes = job_data.operator_notes
    
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job (only while in DRAFT status)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only delete jobs in DRAFT status"
        )
    
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}


@router.post("/{job_id}/submit", response_model=JobResponse)
async def submit_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a job for printing (moves to READY_FOR_PRINT)."""
    from services.pdf_composer import compose_job_pdf
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate job has slots
    if not job.slots:
        raise HTTPException(status_code=400, detail="Job has no slots defined")
    
    # Check all slots have label assets
    for slot in job.slots:
        if not slot.label_asset_path:
            raise HTTPException(
                status_code=400,
                detail=f"Slot {slot.slot_position or slot.template_slot_id} is missing label asset"
            )
    
    # Generate composed PDF
    try:
        pdf_path = compose_job_pdf(job, job.template, db)
        job.composed_pdf_path = pdf_path
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compose PDF: {str(e)}"
        )
    
    if not job.transition_to(JobStatus.READY_FOR_PRINT):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit job from {job.status.value} status"
        )
    
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/slots/{slot_id}/upload")
async def upload_slot_label(
    job_id: int,
    slot_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a label asset for a job slot."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    slot = db.query(JobSlot).filter(
        JobSlot.id == slot_id,
        JobSlot.job_id == job_id
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # Only allow uploads in early stages
    if job.status not in [JobStatus.DRAFT, JobStatus.PENDING_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upload to job in {job.status.value} status"
        )
    
    # Save file
    job_dir = os.path.join(UPLOAD_DIR, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(job_dir, f"slot_{slot_id}{file_ext}")
    
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    slot.label_asset_path = file_path
    db.commit()
    
    return {"message": "Label uploaded", "path": file_path}


@router.get("/{job_id}/download")
async def download_job_pdf(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the composed PDF for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.composed_pdf_path or not os.path.exists(job.composed_pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        job.composed_pdf_path,
        media_type="application/pdf",
        filename=f"job_{job_id}.pdf"
    )


@router.post("/{job_id}/reprint", response_model=JobResponse)
async def create_reprint(
    job_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a reprint of a failed or printed job."""
    original_job = db.query(Job).filter(Job.id == job_id).first()
    if not original_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if original_job.status not in [JobStatus.PRINTED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail="Can only reprint completed or failed jobs"
        )
    
    # Get next queue position
    max_pos = db.query(func.max(Job.queue_position)).filter(
        Job.printer_id == original_job.printer_id
    ).scalar() or 0
    
    # Create new job as copy
    new_job = Job(
        printer_id=original_job.printer_id,
        template_id=original_job.template_id,
        job_name=f"{original_job.job_name} (Reprint)",
        event_name=original_job.event_name,
        event_date=original_job.event_date,
        copies=original_job.copies,
        priority=original_job.priority + 1,  # Higher priority for reprints
        designer_notes=original_job.designer_notes,
        created_by=current_user.id,
        queue_position=max_pos + 1,
        status=JobStatus.READY_FOR_PRINT,  # Skip draft for reprints
        reprint_of=original_job.id,
        reprint_reason=reason,
        composed_pdf_path=original_job.composed_pdf_path,  # Reuse PDF
        submitted_at=datetime.utcnow(),
    )
    db.add(new_job)
    db.flush()
    
    # Copy slots
    for orig_slot in original_job.slots:
        slot = JobSlot(
            job_id=new_job.id,
            template_slot_id=orig_slot.template_slot_id,
            slot_position=orig_slot.slot_position,
            slot_label=orig_slot.slot_label,
            label_asset_path=orig_slot.label_asset_path,
            label_preview_path=orig_slot.label_preview_path,
            guest_name=orig_slot.guest_name,
            recipient=orig_slot.recipient,
            fragrance_id=orig_slot.fragrance_id,
            fragrance_name=orig_slot.fragrance_name,
            product_type=orig_slot.product_type,
        )
        db.add(slot)
    
    db.commit()
    db.refresh(new_job)
    return new_job

