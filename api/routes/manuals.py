import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Manual
from api.schemas import ManualResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manuals", tags=["Manuals"])

@router.get("", response_model=List[ManualResponse])
def list_manuals(
    producto: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists available manuals (metadata only, without the PDF content)."""
    try:
        query = db.query(Manual)
        if producto:
            query = query.filter(Manual.producto == producto.strip())
        return query.order_by(Manual.producto.asc(), Manual.titulo.asc()).all()
    except Exception as e:
        logger.error(f"Error listing manuals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Manuals could not be loaded at this time."
        )

@router.get("/{manual_id}/download")
def download_manual(manual_id: int, db: Session = Depends(get_db)):
    """Downloads the manual PDF (opens inline in the browser)."""
    manual = db.query(Manual).filter(Manual.id == manual_id).first()
    if not manual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual not found.")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", manual.file_name or f"manual-{manual_id}.pdf")
    return Response(
        # Defensive coercion: psycopg v3 may hand BYTEA back as bytes or
        # memoryview depending on the column fetch path; Response requires bytes.
        content=bytes(manual.data),
        media_type=manual.content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'}
    )
