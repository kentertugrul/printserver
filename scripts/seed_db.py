#!/usr/bin/env python3
"""
Seed the database with sample data for development.

Run from the project root:
    python scripts/seed_db.py
"""

import sys
import os
import secrets

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory so SQLite database is created there
os.chdir(backend_path)

# Direct imports from SQLAlchemy
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from enum import Enum
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Database setup
DATABASE_URL = "sqlite:///./scentcraft.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============ Models (inline for seed script) ============

class UserRole(str, Enum):
    ADMIN = "admin"
    DESIGNER = "designer"
    OPERATOR = "operator"
    VIEWER = "viewer"


class JobStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    READY_FOR_PRINT = "ready_for_print"
    QUEUED_LOCAL = "queued_local"
    AWAITING_OPERATOR = "awaiting_operator"
    SENT_TO_PRINTER = "sent_to_printer"
    PRINTED = "printed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.DESIGNER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)


class Printer(Base):
    __tablename__ = "printers"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    api_key = Column(String(64), unique=True, nullable=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HotFolder(Base):
    __tablename__ = "hot_folders"
    id = Column(String(50), primary_key=True)
    printer_id = Column(String(50), ForeignKey("printers.id"), primary_key=True)
    path = Column(Text, nullable=False)
    description = Column(String(200))


class Template(Base):
    __tablename__ = "templates"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    bed_width = Column(Float, nullable=False)
    bed_height = Column(Float, nullable=False)
    hot_folder_type = Column(String(50), nullable=False)
    template_pdf_path = Column(Text)
    template_preview_path = Column(Text)
    preview_image_path = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateSlot(Base):
    __tablename__ = "template_slots"
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    slot_position = Column(String(10))
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    rotation = Column(Float, default=0)
    product_type = Column(String(50))
    display_order = Column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(String(50), ForeignKey("printers.id"), nullable=False)
    template_id = Column(String(50), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    queue_position = Column(Integer)
    local_queue_position = Column(Integer)
    priority = Column(Integer, default=0)
    job_name = Column(String(200))
    event_name = Column(String(200))
    event_date = Column(DateTime)
    copies = Column(Integer, default=1)
    composed_pdf_path = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    reprint_of = Column(Integer)
    reprint_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    downloaded_at = Column(DateTime)
    printed_at = Column(DateTime)
    operator_notes = Column(Text)
    designer_notes = Column(Text)


class JobSlot(Base):
    __tablename__ = "job_slots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    template_slot_id = Column(String(50), nullable=False)
    slot_position = Column(String(10))
    slot_label = Column(String(100))
    label_asset_path = Column(Text)
    label_preview_path = Column(Text)
    guest_name = Column(String(200))
    recipient = Column(String(200))
    fragrance_id = Column(String(50))
    fragrance_name = Column(String(200))
    product_type = Column(String(50))
    qr_uid = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============ Seed Function ============

def seed():
    """Seed database with sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("🌱 Seeding database...")
    
    # Create admin user
    if not db.query(User).filter(User.email == "admin@scentcraft.com").first():
        admin = User(
            email="admin@scentcraft.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        print("  ✓ Created admin user (admin@scentcraft.com / admin123)")
    
    # Create operator user
    if not db.query(User).filter(User.email == "operator@scentcraft.com").first():
        operator = User(
            email="operator@scentcraft.com",
            hashed_password=get_password_hash("operator123"),
            full_name="Print Operator",
            role=UserRole.OPERATOR,
        )
        db.add(operator)
        print("  ✓ Created operator user (operator@scentcraft.com / operator123)")
    
    # Create designer user
    if not db.query(User).filter(User.email == "designer@scentcraft.com").first():
        designer = User(
            email="designer@scentcraft.com",
            hashed_password=get_password_hash("designer123"),
            full_name="Label Designer",
            role=UserRole.DESIGNER,
        )
        db.add(designer)
        print("  ✓ Created designer user (designer@scentcraft.com / designer123)")
    
    db.commit()
    
    # Create printer
    printer = db.query(Printer).filter(Printer.id == "b1070uv-brooklyn").first()
    if not printer:
        api_key = secrets.token_urlsafe(32)
        printer = Printer(
            id="b1070uv-brooklyn",
            name="Epson B1070UV - Brooklyn",
            location="Brooklyn Studio",
            api_key=api_key,
            is_online=False,
        )
        db.add(printer)
        
        # Add hot folders
        hot_folders = [
            HotFolder(
                id="bottle_jig_v1",
                printer_id="b1070uv-brooklyn",
                path="C:\\EdgePrint\\hotfolders\\bottle_jig_v1\\",
                description="30ml bottle + 2x5ml minis + box top",
            ),
            HotFolder(
                id="cards_jig_v1",
                printer_id="b1070uv-brooklyn",
                path="C:\\EdgePrint\\hotfolders\\cards_jig_v1\\",
                description="Business cards and tags",
            ),
        ]
        for hf in hot_folders:
            db.add(hf)
        
        db.commit()
        print(f"  ✓ Created printer: {printer.name}")
        print(f"    API Key: {api_key}")
    else:
        print(f"  • Printer already exists: {printer.name}")
        print(f"    API Key: {printer.api_key}")
    
    # Create template
    template = db.query(Template).filter(Template.id == "bottle_jig_v1").first()
    if not template:
        template = Template(
            id="bottle_jig_v1",
            name="30ml Bottle + 2x Mini + Box",
            description="Standard wedding set: one 30ml bottle, two 5ml minis, and a box top",
            bed_width=329.0,
            bed_height=483.0,
            hot_folder_type="bottle_jig_v1",
        )
        db.add(template)
        
        # Add template slots
        slots = [
            TemplateSlot(
                id="bottle_main",
                template_id="bottle_jig_v1",
                name="30ml Main Bottle",
                slot_position="A",
                x=50.0, y=50.0,
                width=100.0, height=150.0,
                rotation=0,
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
                rotation=0,
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
                rotation=0,
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
                rotation=0,
                product_type="box_top",
                display_order=4,
            ),
        ]
        for slot in slots:
            db.add(slot)
        
        db.commit()
        print(f"  ✓ Created template: {template.name}")
    
    # Create sample jobs
    designer = db.query(User).filter(User.email == "designer@scentcraft.com").first()
    
    # Only create sample jobs if none exist
    existing_jobs = db.query(Job).count()
    if existing_jobs == 0:
        sample_jobs = [
            {
                "job_name": "Sarah & Tom - Table 1",
                "event_name": "Sarah & Tom Wedding",
                "status": JobStatus.QUEUED_LOCAL,
                "slots": [
                    {"template_slot_id": "bottle_main", "slot_position": "A", "slot_label": "30ml Main Bottle", "guest_name": "Sarah", "fragrance_name": "Midnight Rose", "product_type": "30ml_bottle"},
                    {"template_slot_id": "mini_1", "slot_position": "B", "slot_label": "5ml Mini #1", "guest_name": "Sarah - Mini 1", "fragrance_name": "Fresh Linen", "product_type": "5ml_mini"},
                    {"template_slot_id": "mini_2", "slot_position": "C", "slot_label": "5ml Mini #2", "guest_name": "Sarah - Mini 2", "fragrance_name": "Ocean Breeze", "product_type": "5ml_mini"},
                    {"template_slot_id": "box_top", "slot_position": "D", "slot_label": "Box Top", "guest_name": "Sarah", "fragrance_name": None, "product_type": "box_top"},
                ],
            },
            {
                "job_name": "ACME Launch - Set 1",
                "event_name": "ACME Product Launch",
                "status": JobStatus.QUEUED_LOCAL,
                "slots": [
                    {"template_slot_id": "bottle_main", "slot_position": "A", "slot_label": "30ml Main Bottle", "guest_name": "ACME Corp", "fragrance_name": "Executive Blend", "product_type": "30ml_bottle"},
                    {"template_slot_id": "mini_1", "slot_position": "B", "slot_label": "5ml Mini #1", "guest_name": "ACME - Sample A", "fragrance_name": "Morning Dew", "product_type": "5ml_mini"},
                    {"template_slot_id": "mini_2", "slot_position": "C", "slot_label": "5ml Mini #2", "guest_name": "ACME - Sample B", "fragrance_name": "Evening Calm", "product_type": "5ml_mini"},
                    {"template_slot_id": "box_top", "slot_position": "D", "slot_label": "Box Top", "guest_name": "ACME Corp", "fragrance_name": None, "product_type": "box_top"},
                ],
            },
            {
                "job_name": "Emma's Birthday - Gift Set",
                "event_name": "Emma's 30th Birthday",
                "status": JobStatus.QUEUED_LOCAL,
                "slots": [
                    {"template_slot_id": "bottle_main", "slot_position": "A", "slot_label": "30ml Main Bottle", "guest_name": "Emma", "fragrance_name": "Birthday Cake", "product_type": "30ml_bottle"},
                    {"template_slot_id": "mini_1", "slot_position": "B", "slot_label": "5ml Mini #1", "guest_name": "Emma - Travel", "fragrance_name": "Vanilla Dream", "product_type": "5ml_mini"},
                    {"template_slot_id": "mini_2", "slot_position": "C", "slot_label": "5ml Mini #2", "guest_name": "Emma - Purse", "fragrance_name": "Cherry Blossom", "product_type": "5ml_mini"},
                    {"template_slot_id": "box_top", "slot_position": "D", "slot_label": "Box Top", "guest_name": "Happy Birthday Emma!", "fragrance_name": None, "product_type": "box_top"},
                ],
            },
        ]
        
        for i, job_data in enumerate(sample_jobs, 1):
            job = Job(
                printer_id="b1070uv-brooklyn",
                template_id="bottle_jig_v1",
                job_name=job_data["job_name"],
                event_name=job_data["event_name"],
                status=job_data["status"],
                queue_position=i,
                local_queue_position=i,
                copies=1,
                priority=0,
                created_by=designer.id if designer else None,
                composed_pdf_path=f"./uploads/job_{i}/composed.pdf",
            )
            db.add(job)
            db.flush()
            
            # Add slots
            for slot_data in job_data["slots"]:
                slot = JobSlot(
                    job_id=job.id,
                    template_slot_id=slot_data["template_slot_id"],
                    slot_position=slot_data.get("slot_position"),
                    slot_label=slot_data.get("slot_label"),
                    guest_name=slot_data.get("guest_name"),
                    fragrance_name=slot_data.get("fragrance_name"),
                    product_type=slot_data.get("product_type"),
                    label_asset_path="./uploads/placeholder.png",
                )
                db.add(slot)
            
            print(f"  ✓ Created job: {job_data['job_name']}")
        
        db.commit()
    
    db.close()
    
    print()
    print("✨ Database seeded successfully!")
    print()
    print("You can now:")
    print("  1. Start the backend: cd backend && uvicorn main:app --reload --host 0.0.0.0")
    print("  2. Start the console: cd console && npm run dev")
    print("  3. Login with: operator@scentcraft.com / operator123")


if __name__ == "__main__":
    seed()
