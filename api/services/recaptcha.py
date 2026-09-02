import logging
import httpx
from typing import Optional
from api.config import settings

logger = logging.getLogger(__name__)

GOOGLE_RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

async def verify_recaptcha(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """
    Verifica un token de Google reCAPTCHA contra la API de Google.
    En entorno 'development', permite bypass si la clave no está configurada.
    """
    secret = settings.RECAPTCHA_SECRET_KEY
    
    # Modo desarrollo sin clave configurada o con tokens de prueba
    if not secret or secret.startswith("6LeIx0cDtu_"):
        if settings.ENVIRONMENT == "development":
            logger.warning("reCAPTCHA: Sin clave configurada en entorno de desarrollo. Bypass activado.")
            return True
        logger.error("reCAPTCHA: Clave secreta no configurada en entorno de producción.")
        return False

    if not token:
        logger.warning("reCAPTCHA: Token no suministrado.")
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                GOOGLE_RECAPTCHA_VERIFY_URL,
                data={
                    "secret": secret,
                    "response": token,
                    "remoteip": remote_ip or ""
                }
            )
            result = response.json()
            success = result.get("success", False)
            if not success:
                logger.warning(f"reCAPTCHA verificación falló: {result.get('error-codes', [])}")
            return success
    except Exception as e:
        logger.error(f"Error al verificar reCAPTCHA con Google: {e}")
        # En caso de falla de red crítica de Google, decidir según política
        if settings.ENVIRONMENT == "development":
            return True
        return False
