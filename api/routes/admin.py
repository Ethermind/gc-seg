import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from api.database import get_db
from api.models import ContactLead, Review, AdminUser, Manual
from api.schemas import (
    LeadResponse,
    LeadUpdate,
    ContactCreate,
    ReviewResponse,
    ReviewCreate,
    ReviewUpdate,
    AdminUserResponse,
    AdminUserCreate,
    ChangePasswordRequest,
    ManualResponse
)
from api.routes.reviews import generate_avatar_initials
from api.auth import get_current_admin, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# PDF size limit: Vercel serverless functions accept ~4.5 MB per request
MAX_MANUAL_SIZE_BYTES = 4 * 1024 * 1024

# ==============================================================================
# STATS
# ==============================================================================
@router.get("/stats")
def get_dashboard_stats(
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        total_leads = db.query(ContactLead).count()
        new_leads = db.query(ContactLead).filter(ContactLead.status == "nuevo").count()
        total_reviews = db.query(Review).count()
        total_admins = db.query(AdminUser).count()
        avg_rating_res = db.query(func.avg(Review.rating)).scalar() or 5.0

        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "total_reviews": total_reviews,
            "total_admins": total_admins,
            "avg_rating": round(float(avg_rating_res), 1)
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving metrics."
        )

# ==============================================================================
# LEADS / CONTACT REQUESTS CRUD
# ==============================================================================
@router.get("/leads", response_model=List[LeadResponse])
def get_all_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(ContactLead)
        if status_filter and status_filter != "todos":
            query = query.filter(ContactLead.status == status_filter)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ContactLead.nombre.ilike(search_pattern),
                    ContactLead.email.ilike(search_pattern),
                    ContactLead.telefono.ilike(search_pattern),
                    ContactLead.producto.ilike(search_pattern),
                    ContactLead.mensaje.ilike(search_pattern)
                )
            )
        leads = query.order_by(ContactLead.created_at.desc(), ContactLead.id.desc()).all()
        return leads
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying contact requests."
        )

@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead_manual(
    payload: ContactCreate,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        new_lead = ContactLead(
            nombre=payload.nombre,
            telefono=payload.telefono,
            email=payload.email,
            producto=payload.producto,
            mensaje=payload.mensaje,
            wsp_preferred=payload.wsp,
            aceptar_datos=payload.aceptarDatos,
            status="nuevo"
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        return new_lead
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead manually: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating the request."
        )

@router.patch("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    lead = db.query(ContactLead).filter(ContactLead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    try:
        if payload.status is not None:
            lead.status = payload.status
        if payload.mensaje is not None:
            lead.mensaje = payload.mensaje
        if payload.producto is not None:
            lead.producto = payload.producto

        db.commit()
        db.refresh(lead)
        return lead
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating the request.")

@router.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    lead = db.query(ContactLead).filter(ContactLead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    try:
        db.delete(lead)
        db.commit()
        return {"success": True, "message": f"Request #{lead_id} deleted successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting the request.")

# ==============================================================================
# REVIEWS / TESTIMONIALS CRUD
# ==============================================================================
@router.get("/reviews", response_model=List[ReviewResponse])
def get_all_reviews_admin(
    approved_filter: Optional[str] = Query(None, alias="approved"),
    search: Optional[str] = Query(None),
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Review)
        if approved_filter == "true":
            query = query.filter(Review.is_approved == True)
        elif approved_filter == "false":
            query = query.filter(Review.is_approved == False)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Review.name.ilike(search_pattern),
                    Review.role.ilike(search_pattern),
                    Review.text.ilike(search_pattern)
                )
            )
        reviews = query.order_by(Review.created_at.desc(), Review.id.desc()).all()
        return reviews
    except Exception as e:
        logger.error(f"Error listing reviews in admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying reviews."
        )

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review_admin(
    payload: ReviewCreate,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        avatar = generate_avatar_initials(payload.name)
        new_review = Review(
            name=payload.name,
            role=payload.role or "Cliente Asegurado",
            avatar=avatar,
            rating=payload.rating,
            text=payload.text,
            is_approved=payload.is_approved if payload.is_approved is not None else True
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        return new_review
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating review in admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating the review.")

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review_admin(
    review_id: int,
    payload: ReviewUpdate,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

    try:
        if payload.name is not None:
            review.name = payload.name
            review.avatar = generate_avatar_initials(payload.name)
        if payload.role is not None:
            review.role = payload.role
        if payload.rating is not None:
            review.rating = payload.rating
        if payload.text is not None:
            review.text = payload.text
        if payload.is_approved is not None:
            review.is_approved = payload.is_approved

        db.commit()
        db.refresh(review)
        return review
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating review {review_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating the review.")

@router.delete("/reviews/{review_id}")
def delete_review_admin(
    review_id: int,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

    try:
        db.delete(review)
        db.commit()
        return {"success": True, "message": f"Review #{review_id} deleted successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting review {review_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting the review.")

# ==============================================================================
# MANUALS CRUD (PDF per product, stored as blobs in the DB)
# ==============================================================================
@router.get("/manuals", response_model=List[ManualResponse])
def get_all_manuals_admin(
    producto: Optional[str] = Query(None),
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Manual)
        if producto:
            query = query.filter(Manual.producto == producto.strip())
        return query.order_by(Manual.producto.asc(), Manual.titulo.asc()).all()
    except Exception as e:
        logger.error(f"Error listing manuals in admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error querying manuals.")

@router.post("/manuals", response_model=ManualResponse, status_code=status.HTTP_201_CREATED)
async def upload_manual(
    producto: str = Form(...),
    titulo: str = Form(...),
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    producto = (producto or "").strip()
    titulo = (titulo or "").strip()

    if not producto or len(producto) > 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid product.")
    if not titulo or len(titulo) > 150:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A title is required (max 150 characters).")

    is_pdf = (file.content_type == "application/pdf") or (file.filename or "").lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only PDF files are allowed.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The file is empty.")
    if len(data) > MAX_MANUAL_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The PDF exceeds the maximum allowed size of 4 MB."
        )

    try:
        new_manual = Manual(
            producto=producto,
            titulo=titulo,
            file_name=file.filename or f"{titulo}.pdf",
            content_type="application/pdf",
            size_bytes=len(data),
            data=data
        )
        db.add(new_manual)
        db.commit()
        db.refresh(new_manual)
        logger.info(f"Manual #{new_manual.id} uploaded: {titulo} ({producto}, {len(data)} bytes) by {current_user.username}")
        return new_manual
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving manual: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error saving the manual.")

@router.delete("/manuals/{manual_id}")
def delete_manual_admin(
    manual_id: int,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    manual = db.query(Manual).filter(Manual.id == manual_id).first()
    if not manual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual not found.")

    try:
        db.delete(manual)
        db.commit()
        return {"success": True, "message": f"Manual \"{manual.titulo}\" deleted successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting manual {manual_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting the manual.")

# ==============================================================================
# ADMIN USERS CRUD
# ==============================================================================
@router.get("/users", response_model=List[AdminUserResponse])
def get_all_admin_users(
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        users = db.query(AdminUser).order_by(AdminUser.created_at.asc()).all()
        return users
    except Exception as e:
        logger.error(f"Error listing admin users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listing administrators.")

@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    payload: AdminUserCreate,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Check if username or email already exist
    existing = db.query(AdminUser).filter(
        or_(
            AdminUser.username == payload.username,
            AdminUser.email == payload.email
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator with that username or email address already exists."
        )

    try:
        hashed = hash_password(payload.password)
        new_user = AdminUser(
            username=payload.username,
            email=payload.email,
            hashed_password=hashed,
            full_name=payload.full_name or payload.username,
            role=payload.role or "admin",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating administrator.")

@router.put("/users/{user_id}/password")
def change_admin_password(
    user_id: int,
    payload: ChangePasswordRequest,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    try:
        target_user.hashed_password = hash_password(payload.new_password)
        db.commit()
        return {"success": True, "message": f"Password for user {target_user.username} updated successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password of admin {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating the password.")

@router.delete("/users/{user_id}")
def delete_admin_user(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Safeguard 1: no self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own administrator account while you are logged in."
        )

    # Safeguard 2: cannot delete the only remaining administrator
    total_admins = db.query(AdminUser).count()
    if total_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete the only remaining administrator in the system."
        )

    # Role rule 1: only a superadmin can delete another superadmin
    if target_user.role == "superadmin":
        if current_user.role != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a superadministrator can delete another superadministrator."
            )
        # Role rule 2: the system must always keep at least one superadmin
        total_superadmins = db.query(AdminUser).filter(AdminUser.role == "superadmin").count()
        if total_superadmins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete the only superadministrator in the system."
            )

    try:
        db.delete(target_user)
        db.commit()
        return {"success": True, "message": f"Administrator {target_user.username} deleted successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting admin user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting administrator.")
