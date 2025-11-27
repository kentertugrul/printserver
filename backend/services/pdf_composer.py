"""
PDF Composition Service

Composes final print-ready PDFs by overlaying label artwork onto jig template PDFs.

Supports two modes:
1. Template PDF as base - Labels are placed onto your existing jig PDF
2. Blank canvas - Labels are placed on a blank page at defined coordinates
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

from reportlab.lib.pagesizes import A3
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter

# Try to import pdf2image for PDF-to-image conversion (optional dependency)
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


class PDFComposer:
    """
    Composes print-ready PDFs by placing label artwork onto jig templates.
    """
    
    def __init__(self, output_dir: str = "./composed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def compose_job(
        self,
        job_id: int,
        template_pdf_path: Optional[str],
        bed_width_mm: float,
        bed_height_mm: float,
        slots: list[dict],
        output_filename: Optional[str] = None,
    ) -> str:
        """
        Compose a print-ready PDF for a job.
        
        Args:
            job_id: The job ID (for naming)
            template_pdf_path: Path to the jig template PDF (or None for blank)
            bed_width_mm: Print bed width in millimeters
            bed_height_mm: Print bed height in millimeters
            slots: List of slot dicts with keys:
                - x, y, width, height (in mm)
                - rotation (degrees)
                - label_asset_path (path to the label image/PDF)
            output_filename: Custom output filename (optional)
        
        Returns:
            Path to the composed PDF
        """
        output_filename = output_filename or f"job_{job_id}_composed.pdf"
        output_path = self.output_dir / output_filename
        
        # Convert mm to points (1 mm = 2.834645669 points)
        bed_width_pt = bed_width_mm * mm
        bed_height_pt = bed_height_mm * mm
        
        if template_pdf_path and os.path.exists(template_pdf_path):
            # Mode 1: Use template PDF as base
            return self._compose_with_template(
                template_pdf_path=template_pdf_path,
                slots=slots,
                output_path=str(output_path),
                bed_width_pt=bed_width_pt,
                bed_height_pt=bed_height_pt,
            )
        else:
            # Mode 2: Create blank canvas
            return self._compose_blank_canvas(
                slots=slots,
                output_path=str(output_path),
                bed_width_pt=bed_width_pt,
                bed_height_pt=bed_height_pt,
            )
    
    def _compose_with_template(
        self,
        template_pdf_path: str,
        slots: list[dict],
        output_path: str,
        bed_width_pt: float,
        bed_height_pt: float,
    ) -> str:
        """Compose by overlaying labels onto a template PDF."""
        
        # Read the template PDF
        template_reader = PdfReader(template_pdf_path)
        template_page = template_reader.pages[0]
        
        # Get template dimensions
        template_width = float(template_page.mediabox.width)
        template_height = float(template_page.mediabox.height)
        
        # Create overlay PDF with labels
        overlay_buffer = BytesIO()
        overlay_canvas = canvas.Canvas(
            overlay_buffer,
            pagesize=(template_width, template_height)
        )
        
        # Calculate scale factor if template size differs from bed size
        scale_x = template_width / bed_width_pt
        scale_y = template_height / bed_height_pt
        
        # Place each label
        for slot in slots:
            label_path = slot.get("label_asset_path")
            if not label_path or not os.path.exists(label_path):
                continue
            
            # Convert slot coordinates to points and scale
            x_pt = slot["x"] * mm * scale_x
            y_pt = slot["y"] * mm * scale_y
            width_pt = slot["width"] * mm * scale_x
            height_pt = slot["height"] * mm * scale_y
            rotation = slot.get("rotation", 0)
            
            # PDF coordinates are from bottom-left, so flip Y
            y_pt = template_height - y_pt - height_pt
            
            self._place_label(
                canvas=overlay_canvas,
                label_path=label_path,
                x=x_pt,
                y=y_pt,
                width=width_pt,
                height=height_pt,
                rotation=rotation,
            )
        
        overlay_canvas.save()
        overlay_buffer.seek(0)
        
        # Merge template and overlay
        overlay_reader = PdfReader(overlay_buffer)
        overlay_page = overlay_reader.pages[0]
        
        # Merge overlay onto template
        template_page.merge_page(overlay_page)
        
        # Write output
        writer = PdfWriter()
        writer.add_page(template_page)
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        return output_path
    
    def _compose_blank_canvas(
        self,
        slots: list[dict],
        output_path: str,
        bed_width_pt: float,
        bed_height_pt: float,
    ) -> str:
        """Compose on a blank canvas."""
        
        c = canvas.Canvas(output_path, pagesize=(bed_width_pt, bed_height_pt))
        
        # Optional: Add light grid for alignment reference
        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.setLineWidth(0.5)
        grid_spacing = 10 * mm
        
        for x in range(0, int(bed_width_pt), int(grid_spacing)):
            c.line(x, 0, x, bed_height_pt)
        for y in range(0, int(bed_height_pt), int(grid_spacing)):
            c.line(0, y, bed_width_pt, y)
        
        # Place each label
        for slot in slots:
            label_path = slot.get("label_asset_path")
            if not label_path or not os.path.exists(label_path):
                continue
            
            x_pt = slot["x"] * mm
            y_pt = slot["y"] * mm
            width_pt = slot["width"] * mm
            height_pt = slot["height"] * mm
            rotation = slot.get("rotation", 0)
            
            # PDF coordinates are from bottom-left, so flip Y
            y_pt = bed_height_pt - y_pt - height_pt
            
            self._place_label(
                canvas=c,
                label_path=label_path,
                x=x_pt,
                y=y_pt,
                width=width_pt,
                height=height_pt,
                rotation=rotation,
            )
        
        c.save()
        return output_path
    
    def _place_label(
        self,
        canvas: canvas.Canvas,
        label_path: str,
        x: float,
        y: float,
        width: float,
        height: float,
        rotation: float = 0,
    ):
        """Place a label image/PDF onto the canvas."""
        
        canvas.saveState()
        
        # Move to position and rotate if needed
        if rotation != 0:
            # Rotate around the center of the slot
            cx = x + width / 2
            cy = y + height / 2
            canvas.translate(cx, cy)
            canvas.rotate(rotation)
            canvas.translate(-cx, -cy)
        
        # Handle different file types
        ext = os.path.splitext(label_path)[1].lower()
        
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            self._place_image(canvas, label_path, x, y, width, height)
        elif ext == ".pdf":
            self._place_pdf(canvas, label_path, x, y, width, height)
        else:
            # Try as image anyway
            try:
                self._place_image(canvas, label_path, x, y, width, height)
            except Exception:
                pass
        
        canvas.restoreState()
    
    def _place_image(
        self,
        canvas: canvas.Canvas,
        image_path: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ):
        """Place an image onto the canvas, scaling to fit."""
        try:
            img = Image.open(image_path)
            
            # Calculate aspect ratio preserving dimensions
            img_ratio = img.width / img.height
            slot_ratio = width / height
            
            if img_ratio > slot_ratio:
                # Image is wider, fit to width
                draw_width = width
                draw_height = width / img_ratio
                draw_x = x
                draw_y = y + (height - draw_height) / 2
            else:
                # Image is taller, fit to height
                draw_height = height
                draw_width = height * img_ratio
                draw_x = x + (width - draw_width) / 2
                draw_y = y
            
            canvas.drawImage(
                ImageReader(img),
                draw_x, draw_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask='auto',  # Handle transparency
            )
        except Exception as e:
            print(f"Warning: Could not place image {image_path}: {e}")
    
    def _place_pdf(
        self,
        canvas: canvas.Canvas,
        pdf_path: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ):
        """Place a PDF page onto the canvas."""
        try:
            # If pdf2image is available, convert PDF to image first
            if HAS_PDF2IMAGE:
                images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
                if images:
                    img = images[0]
                    # Calculate aspect ratio preserving dimensions
                    img_ratio = img.width / img.height
                    slot_ratio = width / height
                    
                    if img_ratio > slot_ratio:
                        draw_width = width
                        draw_height = width / img_ratio
                        draw_x = x
                        draw_y = y + (height - draw_height) / 2
                    else:
                        draw_height = height
                        draw_width = height * img_ratio
                        draw_x = x + (width - draw_width) / 2
                        draw_y = y
                    
                    canvas.drawImage(
                        ImageReader(img),
                        draw_x, draw_y,
                        width=draw_width,
                        height=draw_height,
                        preserveAspectRatio=True,
                    )
            else:
                # Fallback: draw a placeholder box
                canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
                canvas.setFillColorRGB(0.95, 0.95, 0.95)
                canvas.rect(x, y, width, height, fill=1)
                canvas.setFillColorRGB(0.5, 0.5, 0.5)
                canvas.drawCentredString(
                    x + width / 2,
                    y + height / 2,
                    "PDF Label"
                )
        except Exception as e:
            print(f"Warning: Could not place PDF {pdf_path}: {e}")


def compose_job_pdf(job, template, db) -> str:
    """
    Convenience function to compose a job PDF from database models.
    
    Args:
        job: Job model instance
        template: Template model instance
        db: Database session
    
    Returns:
        Path to the composed PDF
    """
    composer = PDFComposer(output_dir="./composed")
    
    # Build slots list from job slots
    slots = []
    for job_slot in job.slots:
        # Find the template slot for positioning
        template_slot = next(
            (s for s in template.slots if s.id == job_slot.template_slot_id),
            None
        )
        if template_slot:
            slots.append({
                "x": template_slot.x,
                "y": template_slot.y,
                "width": template_slot.width,
                "height": template_slot.height,
                "rotation": template_slot.rotation,
                "label_asset_path": job_slot.label_asset_path,
            })
    
    return composer.compose_job(
        job_id=job.id,
        template_pdf_path=template.template_pdf_path,
        bed_width_mm=template.bed_width,
        bed_height_mm=template.bed_height,
        slots=slots,
        output_filename=f"JOB-{job.id}_{job.event_name or 'print'}.pdf",
    )



