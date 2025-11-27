"""
Operator Console API endpoints.

These endpoints are used by the local operator console to:
- View and manage the local print queue
- Mark jigs as loaded
- Trigger prints
- Mark jobs as complete or failed
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from models import get_db, Job, JobStatus, Printer, User, UserRole
from schemas.job import JobResponse, JobQueueItem, JobReorderRequest
from api.auth import get_current_user, require_role

router = APIRouter()


@router.get("/queue", response_model=List[JobResponse])
async def get_operator_queue(
    printer_id: str,
    db: Session = Depends(get_db),
    # Auth disabled for testing
    # current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))
):
    """
    Get the operator's view of the print queue.
    Shows jobs in QUEUED_LOCAL, AWAITING_OPERATOR, and SENT_TO_PRINTER status.
    """
    # Verify printer exists
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    jobs = db.query(Job).filter(
        Job.printer_id == printer_id,
        Job.status.in_([
            JobStatus.QUEUED_LOCAL,
            JobStatus.AWAITING_OPERATOR,
            JobStatus.SENT_TO_PRINTER,
        ])
    ).order_by(
        Job.local_queue_position.nulls_last(),
        Job.priority.desc(),
        Job.queue_position
    ).all()
    
    return jobs


@router.get("/history", response_model=List[JobResponse])
async def get_print_history(
    printer_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get recent print history (PRINTED and FAILED jobs)."""
    jobs = db.query(Job).filter(
        Job.printer_id == printer_id,
        Job.status.in_([JobStatus.PRINTED, JobStatus.FAILED])
    ).order_by(Job.printed_at.desc()).limit(limit).all()
    
    return jobs


@router.post("/jobs/reorder")
async def reorder_queue(
    printer_id: str,
    reorder: JobReorderRequest,
    db: Session = Depends(get_db),
):
    """
    Reorder jobs in the local queue.
    Accepts a list of job IDs in the desired order.
    """
    # Verify printer exists
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    # Update local_queue_position for each job
    for position, job_id in enumerate(reorder.job_ids, start=1):
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.printer_id == printer_id,
            Job.status.in_([JobStatus.QUEUED_LOCAL, JobStatus.AWAITING_OPERATOR])
        ).first()
        
        if job:
            job.local_queue_position = position
    
    db.commit()
    return {"message": "Queue reordered", "new_order": reorder.job_ids}


@router.post("/jobs/{job_id}/select", response_model=JobResponse)
async def select_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Operator selects a job to work on.
    Shows the jig map and waits for operator to load the jig.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.QUEUED_LOCAL:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be in QUEUED_LOCAL status, currently {job.status.value}"
        )
    
    # No state change here - just returns the job for display
    # The operator uses this to view the jig map
    return job


@router.post("/jobs/{job_id}/jig-loaded", response_model=JobResponse)
async def mark_jig_loaded(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Operator confirms the jig has been loaded according to the slot map.
    Moves job to AWAITING_OPERATOR status.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.QUEUED_LOCAL:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be in QUEUED_LOCAL status, currently {job.status.value}"
        )
    
    if not job.transition_to(JobStatus.AWAITING_OPERATOR):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/print", response_model=JobResponse)
async def trigger_print(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Operator triggers the actual print.
    The agent will copy the PDF to the hot folder.
    Moves job to SENT_TO_PRINTER status.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.AWAITING_OPERATOR:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be in AWAITING_OPERATOR status, currently {job.status.value}"
        )
    
    if not job.transition_to(JobStatus.SENT_TO_PRINTER):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/complete", response_model=JobResponse)
async def mark_complete(
    job_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Operator confirms the print was successful.
    Moves job to PRINTED status.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.SENT_TO_PRINTER:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be in SENT_TO_PRINTER status, currently {job.status.value}"
        )
    
    if not job.transition_to(JobStatus.PRINTED):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    if notes:
        job.operator_notes = (job.operator_notes or "") + f"\n{notes}"
    
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/fail", response_model=JobResponse)
async def mark_failed(
    job_id: int,
    reason: str,
    db: Session = Depends(get_db),
):
    """
    Operator marks a job as failed.
    Can be done from AWAITING_OPERATOR or SENT_TO_PRINTER status.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.AWAITING_OPERATOR, JobStatus.SENT_TO_PRINTER]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot fail job from {job.status.value} status"
        )
    
    if not job.transition_to(JobStatus.FAILED):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    job.operator_notes = (job.operator_notes or "") + f"\nFailed: {reason}"
    
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/return-to-queue", response_model=JobResponse)
async def return_to_queue(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a job from AWAITING_OPERATOR back to QUEUED_LOCAL.
    Used when operator needs to work on a different job first.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.AWAITING_OPERATOR:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be in AWAITING_OPERATOR status"
        )
    
    if not job.transition_to(JobStatus.QUEUED_LOCAL):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    db.commit()
    db.refresh(job)
    return job


