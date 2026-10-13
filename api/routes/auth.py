import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from api.database import get_db
from api.models import AdminUser
from api.schemas import (
    AdminUserCreate,
    AdminUserResponse,
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest
)
from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_admin
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/setup-status")
def get_setup_status(db: Session = Depends(get_db)):
    """Reports whether the system is on its first boot (no administrators)."""
    try:
        total_admins = db.query(AdminUser).count()
        return {
            "needs_setup": total_admins == 0,
            "total_admins": total_admins
        }
    except Exception as e:
        logger.error(f"Error checking setup status: {e}")
        # In case the table does not exist yet
        return {"needs_setup": True, "total_admins": 0}

@router.post("/setup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def setup_first_admin(payload: AdminUserCreate, db: Session = Depends(get_db)):
    """Creates the first admin user with the superadmin role if the table is empty."""
    total = db.query(AdminUser).count()
    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The system already has administrators configured. Please log in."
        )

    try:
        hashed = hash_password(payload.password)
        first_admin = AdminUser(
            username=payload.username.lower().strip(),
            email=payload.email.lower().strip(),
            hashed_password=hashed,
            full_name=payload.full_name or "Principal Administrator",
            role="superadmin",
            is_active=True,
            last_login=datetime.now(timezone.utc)
        )
        db.add(first_admin)
        db.commit()
        db.refresh(first_admin)

        token = create_access_token({
            "sub": first_admin.username,
            "role": first_admin.role,
            "uid": first_admin.id
        })

        logger.info(f"First administrator created successfully: {first_admin.username}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=first_admin
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering first administrator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create the initial administrator."
        )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates an admin user and returns a JWT token."""
    identifier = payload.username.lower().strip()
    user = db.query(AdminUser).filter(
        or_(
            AdminUser.username == identifier,
            AdminUser.email == identifier
        )
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The administrator account is disabled."
        )

    # Update last login timestamp
    try:
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
    except Exception as e:
        logger.warning(f"Could not update last_login: {e}")

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "uid": user.id
    })

    logger.info(f"Successful login: {user.username}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=AdminUserResponse)
def get_current_user_profile(current_user: AdminUser = Depends(get_current_admin)):
    """Returns the profile of the currently authenticated user."""
    return current_user
