from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

# Estados validos del pipeline de solicitudes de cotizacion (lead pipeline)
ALLOWED_LEAD_STATUSES = {"nuevo", "contactado", "en_gestion", "cerrado"}

# Roles validos para usuarios administradores
ALLOWED_ADMIN_ROLES = {"admin", "superadmin"}

# Categorias validas para coberturas
ALLOWED_COVERAGE_CATEGORIES = {"personas", "empresas"}


class ContactCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre y apellido del solicitante")
    telefono: str = Field(..., min_length=6, max_length=50, description="Telefono o WhatsApp de contacto")
    email: Optional[str] = Field(None, max_length=255, description="Correo electronico de contacto")
    producto: Optional[str] = Field(None, max_length=100, description="Tipo de cobertura solicitada")
    mensaje: Optional[str] = Field("", max_length=3000, description="Mensaje o detalle de la consulta")
    wsp: bool = Field(False, description="Preferencia de contacto por WhatsApp")
    aceptarDatos: bool = Field(True, description="Aceptacion de la Ley 25.326 de Proteccion de Datos")
    turnstile_token: Optional[str] = Field(None, description="Token de verificacion Cloudflare Turnstile")

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
                raise ValueError("El formato del correo electronico no es valido.")
            return v
        return None

    @field_validator("telefono")
    def validate_phone(cls, v):
        cleaned = re.sub(r"[^0-9+\s-]", "", v)
        if len(cleaned.strip()) < 6:
            raise ValueError("El numero de telefono debe tener al menos 6 digitos.")
        return cleaned.strip()

    @field_validator("aceptarDatos")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Debe aceptar los terminos de tratamiento de datos personales.")
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
                    f"Estado invalido. Valores permitidos: {', '.join(sorted(ALLOWED_LEAD_STATUSES))}."
                )
        return v


class ReviewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del autor")
    role: Optional[str] = Field("Cliente Asegurado", max_length=100, description="Rol o cobertura del cliente")
    rating: int = Field(..., ge=1, le=5, description="Calificacion de 1 a 5 estrellas")
    text: str = Field(..., min_length=1, max_length=3000, description="Texto de la opinion")
    is_approved: Optional[bool] = True
    turnstile_token: Optional[str] = Field(None, description="Token de verificacion Cloudflare Turnstile")

    @field_validator("name", "role", "text", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ReviewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Calificacion de 1 a 5 estrellas")
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
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario unico")
    email: str = Field(..., max_length=255, description="Correo electronico unico")
    password: str = Field(..., min_length=6, max_length=100, description="Contrasena de acceso")
    full_name: Optional[str] = Field(None, max_length=100, description="Nombre y apellido completo")
    role: Optional[str] = Field("admin", max_length=20, description="Rol del usuario (admin o superadmin)")

    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("El nombre de usuario solo puede contener letras, numeros, puntos, guiones y guiones bajos.")
        return v

    @field_validator("role")
    def validate_role(cls, v):
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_ADMIN_ROLES:
                raise ValueError(
                    f"Rol invalido. Valores permitidos: {', '.join(sorted(ALLOWED_ADMIN_ROLES))}."
                )
        return v

    @field_validator("email")
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Formato de correo electronico invalido.")
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
    username: str = Field(..., description="Nombre de usuario o correo electronico")
    password: str = Field(..., description="Contrasena")


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
    """Metadata de un manual (sin el contenido binario del PDF)."""
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
    categoria: str = Field(..., description="Categoria: 'personas' o 'empresas'")
    titulo: str = Field(..., min_length=1, max_length=100, description="Titulo de la cobertura")
    icono: str = Field(..., min_length=1, max_length=50, description="Nombre del icono Lucide (ej: car, home)")
    descripcion: str = Field(..., min_length=1, description="Descripcion de la cobertura")
    badge: Optional[str] = Field(None, max_length=20, description="Badge opcional (ej: 'Nuevo')")
    orden: int = Field(0, ge=0, description="Orden de visualizacion")
    activo: bool = Field(True, description="Si la cobertura esta activa")

    @field_validator("categoria")
    def validate_categoria(cls, v):
        v = v.strip().lower()
        if v not in ALLOWED_COVERAGE_CATEGORIES:
            raise ValueError(f"Categoria invalida. Valores permitidos: {', '.join(sorted(ALLOWED_COVERAGE_CATEGORIES))}.")
        return v

    @field_validator("titulo", "icono", "descripcion", "badge", mode="before")
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class CoverageCreate(CoverageBase):
    pass


class CoverageUpdate(BaseModel):
    categoria: Optional[str] = Field(None, description="Categoria: 'personas' o 'empresas'")
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
                raise ValueError(f"Categoria invalida. Valores permitidos: {', '.join(sorted(ALLOWED_COVERAGE_CATEGORIES))}.")
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
    pregunta: str = Field(..., min_length=1, description="Pregunta")
    respuesta: str = Field(..., min_length=1, description="Respuesta")
    categoria: Optional[str] = Field(None, max_length=50, description="Categoria opcional para agrupacion")
    orden: int = Field(0, ge=0, description="Orden de visualizacion")
    activo: bool = Field(True, description="Si la FAQ esta activa")

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
