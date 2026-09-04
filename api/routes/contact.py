import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import ContactLead
from api.schemas import ContactCreate, ContactResponse
from api.services.turnstile import verify_turnstile
from api.ratelimit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def submit_contact(
    payload: ContactCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Obtener IP del cliente (considerando proxies de Vercel/Cloudflare)
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() 
        or request.client.host 
        if request.client else None
    )
    user_agent = request.headers.get("user-agent", "")

    # 2. Validar Cloudflare Turnstile
    is_valid_captcha = await verify_turnstile(payload.turnstile_token, client_ip)
    if not is_valid_captcha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación de seguridad (anti-bots) falló. Por favor reintente."
        )

    # 3. Guardar Lead en Base de Datos
    try:
        new_lead = ContactLead(
            nombre=payload.nombre,
            telefono=payload.telefono,
            email=payload.email,
            producto=payload.producto,
            mensaje=payload.mensaje,
            wsp_preferred=payload.wsp,
            aceptar_datos=payload.aceptarDatos,
            ip_address=client_ip,
            user_agent=user_agent,
            status="nuevo"
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)

        logger.info(f"Nuevo contacto registrado exitosamente. ID: {new_lead.id}")
        return ContactResponse(
            success=True,
            message="¡Recibimos tu solicitud con éxito! En breve nos pondremos en contacto.",
            id=new_lead.id
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar solicitud de contacto en DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar tu solicitud. Por favor intenta nuevamente más tarde."
        )
