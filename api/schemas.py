from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

# NOTE: field names in Spanish (nombre, producto, pregunta, categoria, ...) are
# the live JSON contract consumed by the frontend. Do not rename them without
# a coordinated frontend change. Validator messages are returned in 422
# responses and shown to end users of the error surface; they are written in
# English by project convention.

# Valid statuses of the quote request pipeline (lead pipeline)
ALLOWED_LEAD_STATUSES = {"nuevo", "contactado", "en_gestion", "cerrado"}

# Valid roles for admin users
ALLOWED_ADMIN_ROLES = {"admin", "superadmin"}

# Valid categories for coverages
ALLOWED_COVERAGE_CATEGORIES = {"personas", "empresas"}


class ContactCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Full name of the requester")
    telefono: str = Field(..., min_length=6, max_length=50, description="Contact phone or WhatsApp")
    email: Optional[str] = Field(None, max_length=255, description="Contact email address")
    producto: Optional[str] = Field(None, max_length=100, description="Type of coverage requested")
    mensaje: Optional[str] = Field("", max_length=3000, description="Message or inquiry details")
    wsp: bool = Field(False, description="WhatsApp contact preference")
    aceptarDatos: bool = Field(True, description="Acceptance of Law 25.326 on Personal Data Protection")
    turnstile_token: Optional[str] = Field(None, description="Cloudflare Turnstile verification token")

    @field_validator("nombre", "telefono", "producto", "mensaje", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email")
    def validate_email_format(cls, v):
        if v is not None and v != "":
            v = v.strip().lower()
            pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
            if not re.match(pattern, v):
                raise ValueError("Invalid email address format.")
            return v
        return None

    @field_validator("telefono")
    def validate_phone(cls, v):
        cleaned = re.sub(r"[^0-9+\s-]", "", v)
        if len(cleaned.strip()) < 6:
            raise ValueError("The phone number must contain at least 6 digits.")
        return cleaned.strip()

    @field_validator("aceptarDatos")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("You must accept the personal data processing terms.")
        return v


class ContactResponse(BaseModel):
    success: bool
    message: str
    id: Optional[int] = None


class LeadResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    email: Optional[str] = None
    producto: Optional[str] = None
    mensaje: Optional[str] = None
    wsp_preferred: bool = False
    aceptar_datos: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "nuevo"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)
    mensaje: Optional[str] = Field(None, max_length=3000)
    producto: Optional[str] = Field(None, max_length=100)

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_LEAD_STATUSES:
                raise ValueError(
                    f"Invalid status. Allowed values: {', '.join(sorted(ALLOWED_LEAD_STATUSES))}."
                )
        return v


class ReviewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Author name")
    role: Optional[str] = Field("Cliente Asegurado", max_length=100, description="Role or coverage of the client")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    text: str = Field(..., min_length=1, max_length=3000, description="Review text")
    is_approved: Optional[bool] = True
    turnstile_token: Optional[str] = Field(None, description="Cloudflare Turnstile verification token")

    @field_validator("name", "role", "text", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ReviewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    text: Optional[str] = Field(None, min_length=1, max_length=3000)
    is_approved: Optional[bool] = None

    @field_validator("name", "role", "text", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ReviewResponse(BaseModel):
    id: int
    name: str
    role: Optional[str] = "Cliente Asegurado"
    avatar: str
    rating: int
    text: str
    is_approved: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================================================================
# AUTH & ADMIN USER SCHEMAS
# ==============================================================================
class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., max_length=255, description="Unique email address")
    password: str = Field(..., min_length=6, max_length=100, description="Login password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    role: Optional[str] = Field("admin", max_length=20, description="User role (admin or superadmin)")

    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username may only contain letters, numbers, dots, dashes and underscores.")
        return v

    @field_validator("role")
    def validate_role(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_ADMIN_ROLES:
                raise ValueError(
                    f"Invalid role. Allowed values: {', '.join(sorted(ALLOWED_ADMIN_ROLES))}."
                )
        return v

    @field_validator("email")
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email address format.")
        return v


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "admin"
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AdminUserResponse


class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(..., min_length=6, max_length=100)


# ==============================================================================
# MANUALS SCHEMAS
# ==============================================================================
class ManualResponse(BaseModel):
    """Manual metadata (without the binary PDF content)."""
    id: int
    producto: str
    titulo: str
    file_name: str
    content_type: str = "application/pdf"
    size_bytes: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================================================================
# COVERAGES SCHEMAS
# ==============================================================================
class CoverageBase(BaseModel):
    categoria: str = Field(..., description="Category: 'personas' or 'empresas'")
    titulo: str = Field(..., min_length=1, max_length=100, description="Coverage title")
    icono: str = Field(..., min_length=1, max_length=50, description="Lucide icon name (e.g. car, home)")
    descripcion: str = Field(..., min_length=1, description="Coverage description")
    badge: Optional[str] = Field(None, max_length=20, description="Optional badge (e.g. 'Nuevo')")
    orden: int = Field(0, ge=0, description="Display order")
    activo: bool = Field(True, description="Whether the coverage is active")

    @field_validator("categoria")
    def validate_categoria(cls, v):
        v = v.strip().lower()
        if v not in ALLOWED_COVERAGE_CATEGORIES:
            raise ValueError(f"Invalid category. Allowed values: {', '.join(sorted(ALLOWED_COVERAGE_CATEGORIES))}.")
        return v

    @field_validator("titulo", "icono", "descripcion", "badge", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class CoverageCreate(CoverageBase):
    pass


class CoverageUpdate(BaseModel):
    categoria: Optional[str] = Field(None, description="Category: 'personas' or 'empresas'")
    titulo: Optional[str] = Field(None, min_length=1, max_length=100)
    icono: Optional[str] = Field(None, min_length=1, max_length=50)
    descripcion: Optional[str] = Field(None, min_length=1)
    badge: Optional[str] = Field(None, max_length=20)
    orden: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None

    @field_validator("categoria")
    def validate_categoria(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_COVERAGE_CATEGORIES:
                raise ValueError(f"Invalid category. Allowed values: {', '.join(sorted(ALLOWED_COVERAGE_CATEGORIES))}.")
            return v
        return v

    @field_validator("titulo", "icono", "descripcion", "badge", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class CoverageResponse(CoverageBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================================================================
# FAQ SCHEMAS
# ==============================================================================
class FAQBase(BaseModel):
    pregunta: str = Field(..., min_length=1, description="Question")
    respuesta: str = Field(..., min_length=1, description="Answer")
    categoria: Optional[str] = Field(None, max_length=50, description="Optional category for grouping")
    orden: int = Field(0, ge=0, description="Display order")
    activo: bool = Field(True, description="Whether the FAQ is active")

    @field_validator("pregunta", "respuesta", "categoria", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    pregunta: Optional[str] = Field(None, min_length=1)
    respuesta: Optional[str] = Field(None, min_length=1)
    categoria: Optional[str] = Field(None, max_length=50)
    orden: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None

    @field_validator("pregunta", "respuesta", "categoria", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class FAQResponse(FAQBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
