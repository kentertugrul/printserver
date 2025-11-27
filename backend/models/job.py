from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .database import Base


class JobStatus(str, Enum):
    """
    Job lifecycle states:
    
    DRAFT → PENDING_REVIEW → READY_FOR_PRINT → QUEUED_LOCAL → AWAITING_OPERATOR → SENT_TO_PRINTER → PRINTED
                                                                        │                              │
                                                                        └──────────► FAILED ◄─────────┘
    """
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    READY_FOR_PRINT = "ready_for_print"
    QUEUED_LOCAL = "queued_local"
    AWAITING_OPERATOR = "awaiting_operator"
    SENT_TO_PRINTER = "sent_to_printer"
    PRINTED = "printed"
    FAILED = "failed"


# Valid status transitions
VALID_TRANSITIONS = {
    JobStatus.DRAFT: [JobStatus.PENDING_REVIEW, JobStatus.READY_FOR_PRINT],
    JobStatus.PENDING_REVIEW: [JobStatus.READY_FOR_PRINT, JobStatus.DRAFT],
    JobStatus.READY_FOR_PRINT: [JobStatus.QUEUED_LOCAL],
    JobStatus.QUEUED_LOCAL: [JobStatus.AWAITING_OPERATOR, JobStatus.READY_FOR_PRINT],
    JobStatus.AWAITING_OPERATOR: [JobStatus.SENT_TO_PRINTER, JobStatus.QUEUED_LOCAL, JobStatus.FAILED],
    JobStatus.SENT_TO_PRINTER: [JobStatus.PRINTED, JobStatus.FAILED],
    JobStatus.PRINTED: [],  # Terminal state
    JobStatus.FAILED: [JobStatus.READY_FOR_PRINT],  # Can be re-queued
}


class Job(Base):
    """
    Represents a print job - one composed PDF that goes through the print workflow.
    A job contains multiple slots (labels for different items in the jig).
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Assignment
    printer_id = Column(String(50), ForeignKey("printers.id"), nullable=False)
    template_id = Column(String(50), ForeignKey("templates.id"), nullable=False)
    
    # Status and ordering
    status = Column(SQLEnum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    queue_position = Column(Integer)  # Cloud queue order
    local_queue_position = Column(Integer)  # Operator's local reorder
    priority = Column(Integer, default=0)  # Higher = more urgent
    
    # Job metadata
    job_name = Column(String(200))  # e.g., "Sarah & Tom - Wedding - Tray 1"
    event_name = Column(String(200))  # e.g., "Sarah & Tom Wedding"
    event_date = Column(DateTime)
    copies = Column(Integer, default=1)
    
    # Generated files
    composed_pdf_path = Column(Text)  # Path to the final composed PDF
    
    # Creator tracking
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Reprint tracking
    reprint_of = Column(Integer, ForeignKey("jobs.id"))
    reprint_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)  # When moved to READY_FOR_PRINT
    downloaded_at = Column(DateTime)  # When agent downloaded
    printed_at = Column(DateTime)  # When marked as PRINTED
    
    # Notes
    operator_notes = Column(Text)
    designer_notes = Column(Text)
    
    # Relationships
    printer = relationship("Printer", back_populates="jobs")
    template = relationship("Template", back_populates="jobs")
    slots = relationship("JobSlot", back_populates="job", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    original_job = relationship("Job", remote_side=[id], foreign_keys=[reprint_of])

    def can_transition_to(self, new_status: JobStatus) -> bool:
        """Check if transition to new_status is valid."""
        return new_status in VALID_TRANSITIONS.get(self.status, [])
    
    def transition_to(self, new_status: JobStatus) -> bool:
        """
        Attempt to transition to a new status.
        Returns True if successful, False if invalid transition.
        """
        if not self.can_transition_to(new_status):
            return False
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Update relevant timestamps
        if new_status == JobStatus.READY_FOR_PRINT:
            self.submitted_at = datetime.utcnow()
        elif new_status == JobStatus.QUEUED_LOCAL:
            self.downloaded_at = datetime.utcnow()
        elif new_status == JobStatus.PRINTED:
            self.printed_at = datetime.utcnow()
        
        return True



