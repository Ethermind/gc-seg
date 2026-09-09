import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import FAQ
from api.schemas import FAQCreate, FAQUpdate, FAQResponse
from api.routes.auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/faqs", tags=["FAQs"])


# ==============================================================================
# PUBLIC ENDPOINTS
# ==============================================================================
@router.get("", response_model=List[FAQResponse])
def list_faqs(
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    solo_activos: bool = Query(True, description="Solo FAQs activas"),
    db: Session = Depends(get_db)
):
    """Lista FAQs publicamente (para el frontend)."""
    try:
        query = db.query(FAQ)
        if categoria:
            query = query.filter(FAQ.categoria == categoria.strip())
        if solo_activos:
            query = query.filter(FAQ.activo == True)
        return query.order_by(FAQ.orden.asc(), FAQ.id.asc()).all()
    except Exception as e:
        logger.error(f"Error al listar FAQs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron cargar las preguntas frecuentes."
        )


# ==============================================================================
# ADMIN ENDPOINTS (protegidos con JWT)
# ==============================================================================
@router.get("/admin", response_model=List[FAQResponse])
def list_faqs_admin(
    categoria: Optional[str] = Query(None),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista todas las FAQs (incluyendo inactivas) para admin."""
    try:
        query = db.query(FAQ)
        if categoria:
            query = query.filter(FAQ.categoria == categoria.strip())
        return query.order_by(FAQ.orden.asc(), FAQ.id.asc()).all()
    except Exception as e:
        logger.error(f"Error al listar FAQs en admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar FAQs."
        )


@router.post("/admin", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
def create_faq_admin(
    payload: FAQCreate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Crea una nueva FAQ."""
    try:
        new_faq = FAQ(
            pregunta=payload.pregunta,
            respuesta=payload.respuesta,
            categoria=payload.categoria,
            orden=payload.orden,
            activo=payload.activo
        )
        db.add(new_faq)
        db.commit()
        db.refresh(new_faq)
        logger.info(f"FAQ creada: {new_faq.pregunta[:50]}... por {current_user.username}")
        return new_faq
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear FAQ: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la FAQ."
        )


@router.put("/admin/{faq_id}", response_model=FAQResponse)
def update_faq_admin(
    faq_id: int,
    payload: FAQUpdate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Actualiza una FAQ existente."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ no encontrada.")

    try:
        if payload.pregunta is not None:
            faq.pregunta = payload.pregunta
        if payload.respuesta is not None:
            faq.respuesta = payload.respuesta
        if payload.categoria is not None:
            faq.categoria = payload.categoria
        if payload.orden is not None:
            faq.orden = payload.orden
        if payload.activo is not None:
            faq.activo = payload.activo

        db.commit()
        db.refresh(faq)
        return faq
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar FAQ {faq_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar la FAQ.")


@router.delete("/admin/{faq_id}")
def delete_faq_admin(
    faq_id: int,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Elimina una FAQ."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ no encontrada.")

    try:
        db.delete(faq)
        db.commit()
        return {"success": True, "message": f"FAQ eliminada exitosamente."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar FAQ {faq_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar la FAQ.")
