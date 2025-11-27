"""
Database seeding endpoint for development/demo.
Creates sample printers, templates, and jobs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from models import get_db, Printer, Template, TemplateSlot, Job, JobSlot, JobStatus

router = APIRouter()


@router.post("/seed-demo-data")
async def seed_demo_data(db: Session = Depends(get_db)):
    """
    Seed the database with demo data.
    This is for development/demo purposes only.
    """
    created = {"printers": 0, "templates": 0, "jobs": 0}
    
    # Create printer if not exists
    printer = db.query(Printer).filter(Printer.id == "b1070uv-brooklyn").first()
    if not printer:
        printer = Printer(
            id="b1070uv-brooklyn",
            name="Epson B1070UV - Brooklyn",
            location="Brooklyn Studio",
            api_key=secrets.token_urlsafe(32),
            is_online=True,
        )
        db.add(printer)
        created["printers"] += 1
    
    # Create template if not exists
    template = db.query(Template).filter(Template.id == "bottle_jig_v1").first()
    if not template:
        template = Template(
            id="bottle_jig_v1",
            name="30ml Bottle + 2x Mini + Box",
            description="Standard jig for 30ml bottle, two 5ml minis, and box top",
            bed_width=329.0,
            bed_height=483.0,
            hot_folder_type="bottle_jig_v1",
            is_active=True,
        )
        db.add(template)
        db.flush()  # Get the template ID
        
        # Add template slots
        slots = [
            TemplateSlot(
                id="bottle_main",
                template_id="bottle_jig_v1",
                name="30ml Main Bottle",
                slot_position="A",
                x=50.0, y=50.0,
                width=100.0, height=150.0,
                rotation=0.0,
                product_type="30ml_bottle",
                display_order=1,
            ),
            TemplateSlot(
                id="mini_1",
                template_id="bottle_jig_v1",
                name="5ml Mini #1",
                slot_position="B",
                x=200.0, y=50.0,
                width=50.0, height=80.0,
                rotation=0.0,
                product_type="5ml_mini",
                display_order=2,
            ),
            TemplateSlot(
                id="mini_2",
                template_id="bottle_jig_v1",
                name="5ml Mini #2",
                slot_position="C",
                x=200.0, y=150.0,
                width=50.0, height=80.0,
                rotation=0.0,
                product_type="5ml_mini",
                display_order=3,
            ),
            TemplateSlot(
                id="box_top",
                template_id="bottle_jig_v1",
                name="Box Top",
                slot_position="D",
                x=50.0, y=250.0,
                width=150.0, height=100.0,
                rotation=0.0,
                product_type="box_top",
                display_order=4,
            ),
        ]
        for slot in slots:
            db.add(slot)
        created["templates"] += 1
    
    # Create sample jobs if none exist
    existing_jobs = db.query(Job).count()
    if existing_jobs == 0:
        sample_jobs = [
            {
                "job_name": "Sarah & Tom Wedding",
                "event_name": "Wedding - June 15",
                "status": JobStatus.QUEUED_LOCAL,
                "guest_name": "Sarah",
            },
            {
                "job_name": "ACME Corp Launch",
                "event_name": "Product Launch",
                "status": JobStatus.QUEUED_LOCAL,
                "guest_name": "ACME",
            },
            {
                "job_name": "Birthday - Emma",
                "event_name": "Emma's 30th",
                "status": JobStatus.AWAITING_OPERATOR,
                "guest_name": "Emma",
            },
        ]
        
        for i, job_data in enumerate(sample_jobs):
            job = Job(
                printer_id="b1070uv-brooklyn",
                template_id="bottle_jig_v1",
                job_name=job_data["job_name"],
                event_name=job_data["event_name"],
                status=job_data["status"],
                copies=1,
                priority=0,
                queue_position=i + 1,
                local_queue_position=i + 1,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            db.add(job)
            db.flush()
            
            # Add job slots
            job_slots = [
                JobSlot(
                    job_id=job.id,
                    template_slot_id="bottle_main",
                    slot_label="30ml Bottle",
                    slot_position=1,
                    guest_name=job_data["guest_name"],
                    product_type="30ml_bottle",
                ),
                JobSlot(
                    job_id=job.id,
                    template_slot_id="mini_1",
                    slot_label="Mini #1",
                    slot_position=2,
                    guest_name=job_data["guest_name"],
                    product_type="5ml_mini",
                ),
            ]
            for slot in job_slots:
                db.add(slot)
            
            created["jobs"] += 1
    
    db.commit()
    
    return {
        "message": "Demo data seeded successfully",
        "created": created,
    }


@router.get("/printer-api-key/{printer_id}")
async def get_printer_api_key(printer_id: str, db: Session = Depends(get_db)):
    """
    Get a printer's API key for agent setup.
    WARNING: This is for development only - remove in production!
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        return {"error": "Printer not found"}
    return {
        "printer_id": printer.id,
        "printer_name": printer.name,
        "api_key": printer.api_key,
        "warning": "Keep this key secret! Use it in your Print Agent config."
    }


@router.delete("/clear-demo-data")
async def clear_demo_data(db: Session = Depends(get_db)):
    """Clear all demo data from the database."""
    # Delete in correct order due to foreign keys
    db.query(JobSlot).delete()
    db.query(Job).delete()
    db.query(TemplateSlot).delete()
    db.query(Template).delete()
    db.query(Printer).delete()
    db.commit()
    
    return {"message": "All demo data cleared"}

