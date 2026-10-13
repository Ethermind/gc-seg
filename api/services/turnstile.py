import logging
import httpx
from typing import Optional
from api.config import settings

logger = logging.getLogger(__name__)

CLOUDFLARE_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

async def verify_turnstile(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """
    Verifies a Cloudflare Turnstile token against Cloudflare's API.
    In the 'development' environment, bypasses verification when no key is configured.

    Official Cloudflare test keys (useful for development/CI):
      - Secret that always PASSES: 1x0000000000000000000000000000000AA
      - Secret that always FAILS: 2x0000000000000000000000000000000AA
      - Site key that always PASSES: 1x00000000000000000000AA
    """
    secret = settings.TURNSTILE_SECRET_KEY

    # No key configured
    if not secret:
        if settings.ENVIRONMENT == "development":
            logger.warning("Turnstile: No secret key configured in development environment. Bypass enabled.")
            return True
        logger.error("Turnstile: Secret key not configured in production environment.")
        return False

    if not token:
        logger.warning("Turnstile: Token not provided.")
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
                logger.warning(f"Turnstile verification failed: {result.get('error-codes', [])}")
            return success
    except Exception as e:
        logger.error(f"Error verifying Turnstile with Cloudflare: {e}")
        # On a critical Cloudflare network failure, decide per environment policy
        if settings.ENVIRONMENT == "development":
            return True
        return False
