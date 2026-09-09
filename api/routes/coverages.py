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
    categoria: Optional[str] = Query(None, description="Filtrar por categoria: 'personas' o 'empresas'"),
    solo_activos: bool = Query(True, description="Solo coberturas activas"),
    db: Session = Depends(get_db)
):
    """Lista coberturas publicamente (para el frontend)."""
    try:
        query = db.query(Coverage)
        if categoria:
            query = query.filter(Coverage.categoria == categoria.strip().lower())
        if solo_activos:
            query = query.filter(Coverage.activo == True)
        return query.order_by(Coverage.orden.asc(), Coverage.id.asc()).all()
    except Exception as e:
        logger.error(f"Error al listar coberturas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron cargar las coberturas."
        )


# ==============================================================================
# ADMIN ENDPOINTS (protegidos con JWT)
# ==============================================================================
@router.get("/admin", response_model=List[CoverageResponse])
def list_coverages_admin(
    categoria: Optional[str] = Query(None),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista todas las coberturas (incluyendo inactivas) para admin."""
    try:
        query = db.query(Coverage)
        if categoria:
            query = query.filter(Coverage.categoria == categoria.strip().lower())
        return query.order_by(Coverage.orden.asc(), Coverage.id.asc()).all()
    except Exception as e:
        logger.error(f"Error al listar coberturas en admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar coberturas."
        )


@router.post("/admin", response_model=CoverageResponse, status_code=status.HTTP_201_CREATED)
def create_coverage_admin(
    payload: CoverageCreate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Crea una nueva cobertura."""
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
        logger.info(f"Cobertura creada: {new_cov.titulo} ({new_cov.categoria}) por {current_user.username}")
        return new_cov
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear cobertura: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la cobertura."
        )


@router.put("/admin/{coverage_id}", response_model=CoverageResponse)
def update_coverage_admin(
    coverage_id: int,
    payload: CoverageUpdate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Actualiza una cobertura existente."""
    cov = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not cov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cobertura no encontrada.")

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
        logger.error(f"Error al actualizar cobertura {coverage_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar la cobertura.")


@router.delete("/admin/{coverage_id}")
def delete_coverage_admin(
    coverage_id: int,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Elimina una cobertura."""
    cov = db.query(Coverage).filter(Coverage.id == coverage_id).first()
    if not cov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cobertura no encontrada.")

    try:
        db.delete(cov)
        db.commit()
        return {"success": True, "message": f"Cobertura \"{cov.titulo}\" eliminada exitosamente."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar cobertura {coverage_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar la cobertura.")
