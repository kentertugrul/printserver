"""
Print Agent API endpoints.

These endpoints are used by the print agent running on the local printer PC.
The agent authenticates using the printer's API key.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os

from models import get_db, Job, JobStatus, Printer, HotFolder
from schemas.job import JobResponse
from schemas.printer import PrinterHeartbeat

router = APIRouter()


async def verify_agent_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Printer:
    """Verify the agent's API key and return the associated printer."""
    printer = db.query(Printer).filter(Printer.api_key == x_api_key).first()
    if not printer:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return printer


@router.post("/heartbeat")
async def agent_heartbeat(
    data: PrinterHeartbeat,
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Agent heartbeat - updates printer online status and last seen time.
    Called periodically by the agent to indicate it's running.
    """
    printer.is_online = True
    printer.last_seen = datetime.utcnow()
    db.commit()
    
    return {
        "status": "ok",
        "printer_id": printer.id,
        "server_time": datetime.utcnow().isoformat()
    }


@router.get("/jobs", response_model=List[JobResponse])
async def get_pending_jobs(
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Get jobs ready for this printer to download.
    Returns jobs in READY_FOR_PRINT status.
    """
    jobs = db.query(Job).filter(
        Job.printer_id == printer.id,
        Job.status == JobStatus.READY_FOR_PRINT
    ).order_by(
        Job.priority.desc(),
        Job.queue_position
    ).all()
    
    return jobs


@router.get("/jobs/{job_id}/download")
async def download_job_pdf(
    job_id: int,
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Download the composed PDF for a job.
    Only accessible if job belongs to this printer and is in READY_FOR_PRINT status.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.printer_id == printer.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.READY_FOR_PRINT:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not ready for download (status: {job.status.value})"
        )
    
    if not job.composed_pdf_path or not os.path.exists(job.composed_pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        job.composed_pdf_path,
        media_type="application/pdf",
        filename=f"JOB-{job.id}_{job.event_name or 'print'}.pdf"
    )


@router.post("/jobs/{job_id}/mark-downloaded", response_model=JobResponse)
async def mark_job_downloaded(
    job_id: int,
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Mark a job as downloaded by the agent.
    Moves job from READY_FOR_PRINT to QUEUED_LOCAL.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.printer_id == printer.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.READY_FOR_PRINT:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not in READY_FOR_PRINT status (current: {job.status.value})"
        )
    
    if not job.transition_to(JobStatus.QUEUED_LOCAL):
        raise HTTPException(status_code=400, detail="Invalid status transition")
    
    # Set local queue position
    max_local_pos = db.query(func.max(Job.local_queue_position)).filter(
        Job.printer_id == printer.id,
        Job.status.in_([JobStatus.QUEUED_LOCAL, JobStatus.AWAITING_OPERATOR])
    ).scalar() or 0
    job.local_queue_position = max_local_pos + 1
    
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}/print-info")
async def get_print_info(
    job_id: int,
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Get the information needed to send a job to EdgePrint.
    Returns the hot folder path for the job's template.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.printer_id == printer.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.SENT_TO_PRINTER:
        raise HTTPException(
            status_code=400,
            detail="Job must be in SENT_TO_PRINTER status to get print info"
        )
    
    # Get the hot folder for this template
    template = job.template
    hot_folder = db.query(HotFolder).filter(
        HotFolder.printer_id == printer.id,
        HotFolder.id == template.hot_folder_type
    ).first()
    
    if not hot_folder:
        raise HTTPException(
            status_code=404,
            detail=f"No hot folder configured for template type {template.hot_folder_type}"
        )
    
    return {
        "job_id": job.id,
        "hot_folder_path": hot_folder.path,
        "filename": f"JOB-{job.id}_{job.event_name or 'print'}.pdf",
        "local_pdf_path": job.composed_pdf_path,
        "copies": job.copies,
    }


@router.post("/jobs/{job_id}/confirm-sent")
async def confirm_sent_to_printer(
    job_id: int,
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Agent confirms the PDF was successfully copied to the hot folder.
    This is an optional confirmation step.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.printer_id == printer.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.SENT_TO_PRINTER:
        raise HTTPException(
            status_code=400,
            detail="Job must be in SENT_TO_PRINTER status"
        )
    
    # Just log/timestamp the confirmation
    job.operator_notes = (job.operator_notes or "") + f"\nAgent confirmed file sent at {datetime.utcnow().isoformat()}"
    db.commit()
    
    return {"status": "confirmed", "job_id": job_id}


@router.get("/queue-status")
async def get_queue_status(
    db: Session = Depends(get_db),
    printer: Printer = Depends(verify_agent_api_key)
):
    """
    Get a summary of the queue status for this printer.
    Useful for agent status display.
    """
    # Count jobs in each status
    status_counts = {}
    for status in JobStatus:
        count = db.query(func.count(Job.id)).filter(
            Job.printer_id == printer.id,
            Job.status == status
        ).scalar()
        status_counts[status.value] = count
    
    return {
        "printer_id": printer.id,
        "printer_name": printer.name,
        "is_online": printer.is_online,
        "status_counts": status_counts,
        "total_pending": status_counts.get("ready_for_print", 0),
        "total_local_queue": (
            status_counts.get("queued_local", 0) + 
            status_counts.get("awaiting_operator", 0) +
            status_counts.get("sent_to_printer", 0)
        ),
    }


