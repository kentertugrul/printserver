from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets

from models import get_db, Printer, HotFolder, User, UserRole
from schemas.printer import PrinterCreate, PrinterResponse, PrinterUpdate, HotFolderCreate
from api.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[PrinterResponse])
async def list_printers(
    db: Session = Depends(get_db),
):
    """List all printers."""
    return db.query(Printer).all()


@router.post("/", response_model=PrinterResponse)
async def create_printer(
    printer_data: PrinterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Create a new printer (admin only)."""
    # Check if ID exists
    existing = db.query(Printer).filter(Printer.id == printer_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Printer ID already exists")
    
    # Generate API key for the print agent
    api_key = secrets.token_urlsafe(32)
    
    printer = Printer(
        id=printer_data.id,
        name=printer_data.name,
        location=printer_data.location,
        api_key=api_key,
    )
    db.add(printer)
    
    # Add hot folders
    for hf_data in printer_data.hot_folders or []:
        hot_folder = HotFolder(
            id=hf_data.id,
            printer_id=printer_data.id,
            path=hf_data.path,
            description=hf_data.description,
        )
        db.add(hot_folder)
    
    db.commit()
    db.refresh(printer)
    return printer


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(
    printer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific printer."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: str,
    printer_data: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update a printer (admin only)."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if printer_data.name is not None:
        printer.name = printer_data.name
    if printer_data.location is not None:
        printer.location = printer_data.location
    if printer_data.is_online is not None:
        printer.is_online = printer_data.is_online
    
    db.commit()
    db.refresh(printer)
    return printer


@router.delete("/{printer_id}")
async def delete_printer(
    printer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Delete a printer (admin only)."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    db.delete(printer)
    db.commit()
    return {"message": "Printer deleted"}


@router.post("/{printer_id}/hot-folders", response_model=PrinterResponse)
async def add_hot_folder(
    printer_id: str,
    hf_data: HotFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Add a hot folder to a printer (admin only)."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    # Check if hot folder ID exists for this printer
    existing = db.query(HotFolder).filter(
        HotFolder.id == hf_data.id,
        HotFolder.printer_id == printer_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Hot folder ID already exists for this printer")
    
    hot_folder = HotFolder(
        id=hf_data.id,
        printer_id=printer_id,
        path=hf_data.path,
        description=hf_data.description,
    )
    db.add(hot_folder)
    db.commit()
    db.refresh(printer)
    return printer


@router.get("/{printer_id}/api-key")
async def get_printer_api_key(
    printer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get the API key for a printer's agent (admin only)."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"api_key": printer.api_key}


@router.post("/{printer_id}/regenerate-api-key")
async def regenerate_api_key(
    printer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Regenerate the API key for a printer's agent (admin only)."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    printer.api_key = secrets.token_urlsafe(32)
    db.commit()
    return {"api_key": printer.api_key}


