import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Review
from api.schemas import ReviewCreate, ReviewResponse
from api.services.turnstile import verify_turnstile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["Reviews"])

def generate_avatar_initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return "U"

@router.get("", response_model=List[ReviewResponse])
def get_approved_reviews(db: Session = Depends(get_db)):
    try:
        reviews = (
            db.query(Review)
            .filter(Review.is_approved == True)
            .order_by(Review.id.asc())
            .all()
        )
        return reviews
    except Exception as e:
        logger.error(f"Error al obtener opiniones de DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron cargar las opiniones en este momento."
        )

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Obtener IP del cliente
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() 
        or request.client.host 
        if request.client else None
    )

    # 2. Validar Cloudflare Turnstile
    is_valid_captcha = await verify_turnstile(payload.turnstile_token, client_ip)
    if not is_valid_captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación de seguridad (anti-bots) falló. Por favor reintente."
        )

    # 3. Guardar Opinión
    try:
        avatar = generate_avatar_initials(payload.name)
        new_review = Review(
            name=payload.name,
            role=payload.role or "Cliente Asegurado",
            avatar=avatar,
            rating=payload.rating,
            text=payload.text,
            is_approved=True # Auto-aprobado por defecto
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)

        logger.info(f"Nueva opinión registrada exitosamente. ID: {new_review.id}")
        return new_review
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar opinión en DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al guardar tu opinión."
        )
