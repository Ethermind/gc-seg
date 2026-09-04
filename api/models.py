from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, SmallInteger, DateTime, CheckConstraint, LargeBinary
from sqlalchemy.orm import deferred
from api.database import Base

class ContactLead(Base):
    __tablename__ = "contact_leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    producto = Column(String(100), nullable=True, index=True)
    mensaje = Column(Text, nullable=True)
    wsp_preferred = Column(Boolean, default=False, nullable=False)
    aceptar_datos = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="nuevo", index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True,
        nullable=False
    )

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), default="Cliente Asegurado", nullable=True)
    avatar = Column(String(10), nullable=False)
    rating = Column(SmallInteger, nullable=False)
    text = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True,
        nullable=False
    )

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="admin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

class Manual(Base):
    """Manuales de producto en PDF, almacenados como blob en la base de datos."""
    __tablename__ = "manuals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto = Column(String(100), nullable=False, index=True)
    titulo = Column(String(150), nullable=False)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(50), default="application/pdf", nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    # deferred: el blob solo se lee de la DB cuando se descarga el archivo,
    # evitando cargar megabytes en los listados.
    data = deferred(Column(LargeBinary, nullable=False))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
