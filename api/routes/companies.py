"""Insurance companies ("Compañías en las que confiamos") shown in the landing
footer. CRUD from the admin panel; public list + logo download for the site.

Logos are stored as blobs (like manual PDFs) and served by
GET /api/companies/{id}/logo. SVG is intentionally NOT accepted: inline SVG
from user uploads is a stored-XSS vector and we cannot guarantee safe
sanitization server-side.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.auth import get_current_admin
from api.database import get_db
from api.models import Company
from api.schemas import CompanyCreate, CompanyResponse, CompanyUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])

# Logos are small by definition; 1 MB is a generous ceiling.
MAX_LOGO_SIZE_BYTES = 1 * 1024 * 1024

# Raster image types accepted for logos. SVG is excluded on purpose (XSS).
ALLOWED_LOGO_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}


def _company_response(c: Company) -> CompanyResponse:
    # Built manually: reading `logo` would load the deferred blob from the DB;
    # `logo_content_type` alone is enough to know whether a logo exists.
    return CompanyResponse(
        id=c.id,
        nombre=c.nombre,
        url=c.url,
        has_logo=bool(c.logo_content_type),
        logo_content_type=c.logo_content_type,
        orden=c.orden,
        activo=c.activo,
        created_at=c.created_at,
    )


def _validate_logo_upload(file: UploadFile, data: bytes) -> str:
    """Returns the normalized content_type for a valid logo, or raises 422/413."""
    declared = (file.content_type or "").lower().split(";")[0].strip()
    name = (file.filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""

    ext_to_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                   "webp": "image/webp", "gif": "image/gif"}
    if ext in ext_to_type:
        content_type = ext_to_type[ext]  # extension wins (same policy as manuals)
    elif declared in ALLOWED_LOGO_CONTENT_TYPES:
        content_type = declared
    else:
        logger.warning("Logo upload rejected (unsupported type): filename='%s' content_type='%s'",
                       file.filename, file.content_type)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El logo debe ser una imagen PNG, JPG, WEBP o GIF (los SVG no están permitidos por seguridad)."
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo de logo está vacío."
        )
    if len(data) > MAX_LOGO_SIZE_BYTES:
        logger.warning("Logo upload rejected (too large): filename='%s' size=%d limit=%d",
                       file.filename, len(data), MAX_LOGO_SIZE_BYTES)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El logo supera el máximo permitido de 1 MB."
        )
    return content_type


# ==============================================================================
# PUBLIC ENDPOINTS
# ==============================================================================
@router.get("", response_model=List[CompanyResponse])
def list_companies(
    solo_activos: bool = Query(True, description="Only active companies"),
    db: Session = Depends(get_db),
):
    """Lists companies publicly (ordered for the landing footer)."""
    try:
        query = db.query(Company)
        if solo_activos:
            query = query.filter(Company.activo == True)
        companies = query.order_by(Company.orden.asc(), Company.id.asc()).all()
        return [_company_response(c) for c in companies]
    except Exception:
        logger.exception("Error listing companies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Companies could not be loaded."
        )


@router.get("/{company_id}/logo")
def download_logo(company_id: int, db: Session = Depends(get_db)):
    """Serves the company logo image (opens inline, cacheable)."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.logo_content_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logo not found.")

    # Defensive coercion: psycopg v3 may hand BYTEA back as bytes or memoryview.
    content = bytes(company.logo or b"")
    return Response(
        content=content,
        media_type=company.logo_content_type,
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "public, max-age=300",
        },
    )


# ==============================================================================
# ADMIN ENDPOINTS (protected with JWT)
# ==============================================================================
@router.get("/admin", response_model=List[CompanyResponse])
def list_companies_admin(
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lists all companies (including inactive ones) for the admin panel."""
    try:
        companies = db.query(Company).order_by(Company.orden.asc(), Company.id.asc()).all()
        return [_company_response(c) for c in companies]
    except Exception:
        logger.exception("Error listing companies in admin")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying companies."
        )


@router.post("/admin", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company_admin(
    nombre: str = Form(...),
    url: Optional[str] = Form(None),
    orden: int = Form(0),
    activo: bool = Form(True),
    logo: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Creates a company. The logo is optional (multipart form, like manuals)."""
    nombre = (nombre or "").strip()
    url = (url or "").strip() or None
    if not nombre or len(nombre) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El nombre de la compañía es obligatorio (máx. 100 caracteres)."
        )
    if url and not url.lower().startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La URL debe comenzar con http:// o https://."
        )

    logo_data, logo_type = None, None
    if logo is not None and (logo.filename or "").strip():
        logo_data = await logo.read()
        logo_type = _validate_logo_upload(logo, logo_data)

    try:
        new_company = Company(
            nombre=nombre,
            url=url,
            orden=orden if orden is not None and orden >= 0 else 0,
            activo=bool(activo),
            logo=logo_data,
            logo_content_type=logo_type,
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        logger.info("Company #%s created: '%s' (logo=%s) by %s",
                    new_company.id, nombre, bool(logo_type), current_user.username)
        return _company_response(new_company)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Error creating company '%s'", nombre)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating the company."
        )


@router.put("/admin/{company_id}", response_model=CompanyResponse)
def update_company_admin(
    company_id: int,
    payload: CompanyUpdate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Updates name/url/order/active of a company (logo has its own endpoint)."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    try:
        if payload.nombre is not None:
            company.nombre = payload.nombre
        if payload.url is not None:
            company.url = payload.url
        if payload.orden is not None:
            company.orden = payload.orden
        if payload.activo is not None:
            company.activo = payload.activo
        db.commit()
        db.refresh(company)
        logger.info("Company #%s updated by %s", company_id, current_user.username)
        return _company_response(company)
    except Exception:
        db.rollback()
        logger.exception("Error updating company %s", company_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating the company."
        )


@router.put("/admin/{company_id}/logo", response_model=CompanyResponse)
async def upload_company_logo(
    company_id: int,
    logo: UploadFile = File(...),
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Sets or replaces the logo of a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    data = await logo.read()
    content_type = _validate_logo_upload(logo, data)
    try:
        company.logo = data
        company.logo_content_type = content_type
        db.commit()
        db.refresh(company)
        logger.info("Logo uploaded for company #%s (%d bytes, %s) by %s",
                    company_id, len(data), content_type, current_user.username)
        return _company_response(company)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Error storing logo for company %s", company_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error storing the logo."
        )


@router.delete("/admin/{company_id}/logo", response_model=CompanyResponse)
def delete_company_logo(
    company_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Removes the logo of a company (it will fall back to the name on the landing)."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    try:
        had_logo = bool(company.logo_content_type)
        company.logo = None
        company.logo_content_type = None
        db.commit()
        db.refresh(company)
        logger.info("Logo removed for company #%s (had_logo=%s) by %s",
                    company_id, had_logo, current_user.username)
        return _company_response(company)
    except Exception:
        db.rollback()
        logger.exception("Error removing logo for company %s", company_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing the logo."
        )


@router.delete("/admin/{company_id}")
def delete_company_admin(
    company_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Deletes a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    try:
        db.delete(company)
        db.commit()
        logger.info("Company #%s ('%s') deleted by %s", company_id, company.nombre, current_user.username)
        return {"success": True, "message": f'Compañía "{company.nombre}" eliminada.'}
    except Exception:
        db.rollback()
        logger.exception("Error deleting company %s", company_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting the company."
        )
