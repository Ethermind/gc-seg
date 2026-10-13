import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Coverage
from api.schemas import CoverageCreate, CoverageUpdate, CoverageResponse
from api.routes.auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coverages", tags=["Coverages"])


# ==============================================================================
# PUBLIC ENDPOINTS
# ==============================================================================
@router.get("", response_model=List[CoverageResponse])
def list_coverages(
    categoria: Optional[str] = Query(None, description="Filter by category: 'personas' or 'empresas'"),
    solo_activos: bool = Query(True, description="Only active coverages"),
    db: Session = Depends(get_db)
):
    """Lists coverages publicly (for the frontend)."""
    try:
        query = db.query(Coverage)
        if categoria:
            query = query.filter(Coverage.categoria == categoria.strip().lower())
        if solo_activos:
            query = query.filter(Coverage.activo == True)
        return query.order_by(Coverage.orden.asc(), Coverage.id.asc()).all()
    except Exception as e:
        logger.error(f"Error listing coverages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Coverages could not be loaded."
        )


# ==============================================================================
# ADMIN ENDPOINTS (protected with JWT)
# ==============================================================================
@router.get("/admin", response_model=List[CoverageResponse])
def list_coverages_admin(
    categoria: Optional[str] = Query(None),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lists all coverages (including inactive ones) for the admin panel."""
    try:
        query = db.query(Coverage)
        if categoria:
            query = query.filter(Coverage.categoria == categoria.strip().lower())
        return query.order_by(Coverage.orden.asc(), Coverage.id.asc()).all()
    except Exception as e:
        logger.error(f"Error listing coverages in admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying coverages."
        )


@router.post("/admin", response_model=CoverageResponse, status_code=status.HTTP_201_CREATED)
def create_coverage_admin(
    payload: CoverageCreate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Creates a new coverage."""
    try:
        new_cov = Coverage(
            categoria=payload.categoria,
            titulo=payload.titulo,
            icono=payload.icono,
            descripcion=payload.descripcion,
            badge=payload.badge,
            orden=payload.orden,
            activo=payload.activo
        )
        db.add(new_cov)
        db.commit()
        db.refresh(new_cov)
        logger.info(f"Coverage created: {new_cov.titulo} ({new_cov.categoria}) by {current_user.username}")
        return new_cov
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating coverage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating the coverage."
        )


@router.put("/admin/{coverage_id}", response_model=CoverageResponse)
def update_coverage_admin(
    coverage_id: int,
    payload: CoverageUpdate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Updates an existing coverage."""
    cov = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not cov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coverage not found.")

    try:
        if payload.categoria is not None:
            cov.categoria = payload.categoria
        if payload.titulo is not None:
            cov.titulo = payload.titulo
        if payload.icono is not None:
            cov.icono = payload.icono
        if payload.descripcion is not None:
            cov.descripcion = payload.descripcion
        if payload.badge is not None:
            cov.badge = payload.badge
        if payload.orden is not None:
            cov.orden = payload.orden
        if payload.activo is not None:
            cov.activo = payload.activo

        db.commit()
        db.refresh(cov)
        return cov
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating coverage {coverage_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating the coverage.")


@router.delete("/admin/{coverage_id}")
def delete_coverage_admin(
    coverage_id: int,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Deletes a coverage."""
    cov = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not cov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coverage not found.")

    try:
        db.delete(cov)
        db.commit()
        return {"success": True, "message": f"Coverage \"{cov.titulo}\" deleted successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting coverage {coverage_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting the coverage.")
