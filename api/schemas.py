from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

# Estados válidos del pipeline de solicitudes de cotización (lead pipeline)
ALLOWED_LEAD_STATUSES = {"nuevo", "contactado", "en_gestion", "cerrado"}

# Roles válidos para usuarios administradores
ALLOWED_ADMIN_ROLES = {"admin", "superadmin"}

class ContactCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre y apellido del solicitante")
    telefono: str = Field(..., min_length=6, max_length=50, description="Teléfono o WhatsApp de contacto")
    email: Optional[str] = Field(None, max_length=255, description="Correo electrónico de contacto")
    producto: Optional[str] = Field(None, max_length=100, description="Tipo de cobertura solicitada")
    mensaje: Optional[str] = Field("", max_length=3000, description="Mensaje o detalle de la consulta")
    wsp: bool = Field(False, description="Preferencia de contacto por WhatsApp")
    aceptarDatos: bool = Field(True, description="Aceptación de la Ley 25.326 de Protección de Datos")
    turnstile_token: Optional[str] = Field(None, description="Token de verificación Cloudflare Turnstile")

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
                raise ValueError("El formato del correo electrónico no es válido.")
            return v
        return None

    @field_validator("telefono")
    def validate_phone(cls, v):
        cleaned = re.sub(r"[^0-9+\s-]", "", v)
        if len(cleaned.strip()) < 6:
            raise ValueError("El número de teléfono debe tener al menos 6 dígitos.")
        return cleaned.strip()

    @field_validator("aceptarDatos")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Debe aceptar los términos de tratamiento de datos personales.")
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
                    f"Estado inválido. Valores permitidos: {', '.join(sorted(ALLOWED_LEAD_STATUSES))}."
                )
        return v

class ReviewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del autor")
    role: Optional[str] = Field("Cliente Asegurado", max_length=100, description="Rol o cobertura del cliente")
    rating: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5 estrellas")
    text: str = Field(..., min_length=1, max_length=3000, description="Texto de la opinión")
    is_approved: Optional[bool] = True
    turnstile_token: Optional[str] = Field(None, description="Token de verificación Cloudflare Turnstile")

    @field_validator("name", "role", "text", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class ReviewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Calificación de 1 a 5 estrellas")
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
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")
    email: str = Field(..., max_length=255, description="Correo electrónico único")
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña de acceso")
    full_name: Optional[str] = Field(None, max_length=100, description="Nombre y apellido completo")
    role: Optional[str] = Field("admin", max_length=20, description="Rol del usuario (admin o superadmin)")

    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos.")
        return v

    @field_validator("role")
    def validate_role(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_ADMIN_ROLES:
                raise ValueError(
                    f"Rol inválido. Valores permitidos: {', '.join(sorted(ALLOWED_ADMIN_ROLES))}."
                )
        return v

    @field_validator("email")
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Formato de correo electrónico inválido.")
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
    username: str = Field(..., description="Nombre de usuario o correo electrónico")
    password: str = Field(..., description="Contraseña")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AdminUserResponse

class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(..., min_length=6, max_length=100)
