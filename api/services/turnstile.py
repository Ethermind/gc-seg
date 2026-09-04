import logging
import httpx
from typing import Optional
from api.config import settings

logger = logging.getLogger(__name__)

CLOUDFLARE_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

async def verify_turnstile(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """
    Verifica un token de Cloudflare Turnstile contra la API de Cloudflare.
    En entorno 'development', permite bypass si la clave no está configurada.

    Claves de prueba oficiales de Cloudflare (útiles en desarrollo/CI):
      - Secret que siempre APRUEBA: 1x0000000000000000000000000000000AA
      - Secret que siempre RECHAZA: 2x0000000000000000000000000000000AA
      - Site key que siempre APRUEBA: 1x00000000000000000000AA
    """
    secret = settings.TURNSTILE_SECRET_KEY

    # Sin clave configurada
    if not secret:
        if settings.ENVIRONMENT == "development":
            logger.warning("Turnstile: Sin clave configurada en entorno de desarrollo. Bypass activado.")
            return True
        logger.error("Turnstile: Clave secreta no configurada en entorno de producción.")
        return False

    if not token:
        logger.warning("Turnstile: Token no suministrado.")
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                CLOUDFLARE_TURNSTILE_VERIFY_URL,
                data={
                    "secret": secret,
                    "response": token,
                    "remoteip": remote_ip or ""
                }
            )
            result = response.json()
            success = result.get("success", False)
            if not success:
                logger.warning(f"Turnstile verificación falló: {result.get('error-codes', [])}")
            return success
    except Exception as e:
        logger.error(f"Error al verificar Turnstile con Cloudflare: {e}")
        # En caso de falla de red crítica de Cloudflare, decidir según política
        if settings.ENVIRONMENT == "development":
            return True
        return False
