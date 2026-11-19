"""Backup & restore of all site data (admin only).

EXPORT (GET /api/admin/backup/export):
    Returns a JSON document with every table EXCEPT the manual PDF binaries
    (manuals are listed as metadata only). The frontend assembles the final
    backup file by fetching each PDF via the existing download endpoint and
    embedding it as base64. This keeps every individual HTTP response small
    (no server-side multi-MB response, which Vercel may truncate).

RESTORE (POST /api/admin/backup/restore + POST /api/admin/backup/restore/manuals/{id}):
    Two-phase restore, deliberately split to respect the ~4.5 MB request body
    limit of Vercel serverless functions:
      1. JSON metadata call: replaces coverages, faqs, reviews, contact_leads
         and manuals metadata (ids preserved), and upserts admin_users.
      2. One multipart call per manual to upload the PDF binary.
    After inserting rows with explicit ids, every id sequence is resynced
    (setval) — inserting explicit ids does NOT advance SERIAL sequences and
    later inserts would collide (see BUGS.md, hotfix 12/10/2026).
"""
import logging
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import text, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth import get_current_admin
from api.database import get_db
from api.models import ContactLead, Review, AdminUser, Manual, Coverage, FAQ
from api.routes.admin import MAX_MANUAL_SIZE_BYTES
from api.schemas import BackupRestore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/backup", tags=["Backup"])

BACKUP_VERSION = 1

# Tables that are wiped and re-inserted verbatim (with their original ids)
# during a restore. admin_users is handled separately: it is upserted by
# username and the restoring operator is never deleted, so the session that
# triggered the restore always survives.
_RESTORED_TABLES = ["coverages", "faqs", "reviews", "contact_leads", "manuals"]


def _require_superadmin(current_user: AdminUser) -> None:
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a superadministrator can restore backups.",
        )


def _iso(dt) -> str:
    return dt.isoformat() if dt else None


@router.get("/summary")
def backup_summary(
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Live counts of every backed-up table, shown on the backup page."""
    try:
        total_bytes = db.query(func.coalesce(func.sum(Manual.size_bytes), 0)).scalar()
        return {
            "leads": db.query(ContactLead).count(),
            "reviews": db.query(Review).count(),
            "coverages": db.query(Coverage).count(),
            "faqs": db.query(FAQ).count(),
            "manuals": db.query(Manual).count(),
            "admin_users": db.query(AdminUser).count(),
            "manuals_total_bytes": int(total_bytes or 0),
        }
    except Exception:
        logger.exception("Error computing backup summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error computing the backup summary."
        )


@router.get("/export")
def export_backup(
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Full data export as JSON (metadata only; PDF binaries are fetched
    separately by the frontend and embedded as base64)."""
    try:
        coverages = [
            {
                "id": c.id, "categoria": c.categoria, "titulo": c.titulo,
                "icono": c.icono, "descripcion": c.descripcion,
                "badge": c.badge, "orden": c.orden, "activo": c.activo,
                "created_at": _iso(c.created_at),
            }
            for c in db.query(Coverage).order_by(Coverage.id.asc()).all()
        ]
        faqs = [
            {
                "id": f.id, "pregunta": f.pregunta, "respuesta": f.respuesta,
                "categoria": f.categoria, "orden": f.orden, "activo": f.activo,
                "created_at": _iso(f.created_at),
            }
            for f in db.query(FAQ).order_by(FAQ.id.asc()).all()
        ]
        reviews = [
            {
                "id": r.id, "name": r.name, "role": r.role, "avatar": r.avatar,
                "rating": r.rating, "text": r.text, "is_approved": r.is_approved,
                "created_at": _iso(r.created_at),
            }
            for r in db.query(Review).order_by(Review.id.asc()).all()
        ]
        leads = [
            {
                "id": l.id, "nombre": l.nombre, "telefono": l.telefono,
                "email": l.email, "producto": l.producto, "mensaje": l.mensaje,
                "wsp_preferred": l.wsp_preferred, "aceptar_datos": l.aceptar_datos,
                "ip_address": l.ip_address, "user_agent": l.user_agent,
                "status": l.status, "created_at": _iso(l.created_at),
            }
            for l in db.query(ContactLead).order_by(ContactLead.id.asc()).all()
        ]
        admin_users = [
            {
                "id": u.id, "username": u.username, "email": u.email,
                "hashed_password": u.hashed_password, "full_name": u.full_name,
                "role": u.role, "is_active": u.is_active,
                "created_at": _iso(u.created_at), "last_login": _iso(u.last_login),
            }
            for u in db.query(AdminUser).order_by(AdminUser.id.asc()).all()
        ]
        manuals = [
            {
                "id": m.id, "producto": m.producto, "titulo": m.titulo,
                "file_name": m.file_name, "content_type": m.content_type,
                "size_bytes": m.size_bytes, "created_at": _iso(m.created_at),
            }
            for m in db.query(Manual).order_by(Manual.id.asc()).all()
        ]

        payload = {
            "meta": {
                "app": "gc-seg",
                "version": BACKUP_VERSION,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "counts": {
                    "coverages": len(coverages), "faqs": len(faqs),
                    "reviews": len(reviews), "leads": len(leads),
                    "admin_users": len(admin_users), "manuals": len(manuals),
                },
            },
            "coverages": coverages,
            "faqs": faqs,
            "reviews": reviews,
            "leads": leads,
            "admin_users": admin_users,
            "manuals": manuals,
        }
        logger.info(
            "Backup exported by %s: %s", current_user.username, payload["meta"]["counts"]
        )
        return payload
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error exporting backup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting the backup."
        )


def _resync_sequence(db: Session, table: str) -> None:
    """Advances the SERIAL sequence past the highest restored id, so future
    inserts never collide. Table names come from a fixed allowlist only."""
    assert table in _RESTORED_TABLES + ["admin_users"]
    row = db.execute(text(f'SELECT COALESCE(MAX(id), 0) AS max_id FROM "{table}"')).scalar()
    seq = db.execute(
        text("SELECT pg_get_serial_sequence(:t, 'id')"), {"t": table}
    ).scalar()
    if not seq:
        return
    if row and row > 0:
        db.execute(text("SELECT setval(:seq, :val, true)"), {"seq": seq, "val": row})
    else:
        db.execute(text("SELECT setval(:seq, 1, false)"), {"seq": seq})


@router.post("/restore")
def restore_backup(
    payload: BackupRestore,
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Replaces all site data with the backup contents. Requires superadmin.

    - coverages/faqs/reviews/leads/manuals: wiped and re-inserted with their
      original ids (manual PDF binaries restored separately, phase 2).
    - admin_users: upserted by username; the current operator is never
      deleted, so the session stays alive even if the backup predates them.
    """
    _require_superadmin(current_user)

    if payload.meta.app != "gc-seg":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This file is not a Giaconi-Capra backup (invalid 'meta.app')."
        )
    if payload.meta.version > BACKUP_VERSION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"The backup version ({payload.meta.version}) is newer than the "
                f"supported version ({BACKUP_VERSION}). Update the site first."
            )
        )

    try:
        # 1. Wipe all replaceable tables.
        db.query(Coverage).delete(synchronize_session=False)
        db.query(FAQ).delete(synchronize_session=False)
        db.query(Review).delete(synchronize_session=False)
        db.query(ContactLead).delete(synchronize_session=False)
        db.query(Manual).delete(synchronize_session=False)

        # 2. Re-insert with original ids (manuals: empty blob placeholder,
        #    binary arrives in phase 2).
        for c in payload.coverages:
            db.add(Coverage(
                id=c.id, categoria=c.categoria, titulo=c.titulo, icono=c.icono,
                descripcion=c.descripcion, badge=c.badge, orden=c.orden,
                activo=c.activo, created_at=c.created_at,
            ))
        for f in payload.faqs:
            db.add(FAQ(
                id=f.id, pregunta=f.pregunta, respuesta=f.respuesta,
                categoria=f.categoria, orden=f.orden, activo=f.activo,
                created_at=f.created_at,
            ))
        for r in payload.reviews:
            db.add(Review(
                id=r.id, name=r.name, role=r.role, avatar=r.avatar,
                rating=r.rating, text=r.text, is_approved=r.is_approved,
                created_at=r.created_at,
            ))
        for l in payload.leads:
            db.add(ContactLead(
                id=l.id, nombre=l.nombre, telefono=l.telefono, email=l.email,
                producto=l.producto, mensaje=l.mensaje,
                wsp_preferred=l.wsp_preferred, aceptar_datos=l.aceptar_datos,
                ip_address=l.ip_address, user_agent=l.user_agent,
                status=l.status, created_at=l.created_at,
            ))
        for m in payload.manuals:
            db.add(Manual(
                id=m.id, producto=m.producto, titulo=m.titulo,
                file_name=m.file_name, content_type=m.content_type,
                size_bytes=0, data=b"", created_at=m.created_at,
            ))

        # 3. admin_users: upsert by username. The operator's own row is always
        #    kept so the current JWT stays valid after the restore.
        backup_usernames = {u.username for u in payload.admin_users}
        for u in payload.admin_users:
            existing = db.query(AdminUser).filter(AdminUser.username == u.username).first()
            if existing:
                existing.email = u.email
                existing.hashed_password = u.hashed_password
                existing.full_name = u.full_name
                existing.role = u.role
                existing.is_active = u.is_active
                existing.created_at = u.created_at or existing.created_at
                existing.last_login = u.last_login
            else:
                db.add(AdminUser(
                    username=u.username, email=u.email,
                    hashed_password=u.hashed_password, full_name=u.full_name,
                    role=u.role, is_active=u.is_active,
                    created_at=u.created_at, last_login=u.last_login,
                ))
        for au in db.query(AdminUser).all():
            if au.username not in backup_usernames and au.username != current_user.username:
                logger.warning(
                    "Restore removes admin user '%s' (not present in backup)", au.username
                )
                db.delete(au)

        # 4. Resync every id sequence (explicit-id inserts do not advance SERIAL).
        # NOTE: SessionLocal uses autoflush=False, so the pending INSERTs must be
        # flushed first — otherwise MAX(id) sees the freshly emptied tables and
        # rewinds the sequence, and the very next insert collides (duplicate key).
        # setval is non-transactional in PostgreSQL: it must run BEFORE commit.
        db.flush()
        for table in _RESTORED_TABLES + ["admin_users"]:
            _resync_sequence(db, table)

        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("Backup restore failed (integrity): %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The backup file is inconsistent (duplicate ids or emails). Restore aborted."
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Error restoring backup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error restoring the backup."
        )

    restored_counts: Dict[str, int] = {
        "coverages": len(payload.coverages),
        "faqs": len(payload.faqs),
        "reviews": len(payload.reviews),
        "leads": len(payload.leads),
        "manuals": len(payload.manuals),
        "admin_users": len(backup_usernames),
    }
    pending_bins = [m.id for m in payload.manuals if m.size_bytes > 0]
    logger.info(
        "Backup metadata restored by %s: %s (binaries pending: %s)",
        current_user.username, restored_counts, pending_bins,
    )
    return {
        "success": True,
        "restored": restored_counts,
        "manuals_pending_binaries": pending_bins,
    }


@router.post("/restore/manuals/{manual_id}")
async def restore_manual_binary(
    manual_id: int,
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Phase 2 of restore: uploads the PDF binary of one restored manual."""
    _require_superadmin(current_user)

    manual = db.query(Manual).filter(Manual.id == manual_id).first()
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manual #{manual_id} does not exist (run the metadata restore first)."
        )

    file_name = file.filename or manual.file_name
    is_pdf = (file.content_type == "application/pdf") or file_name.lower().endswith(".pdf")
    if not is_pdf:
        logger.warning(
            "Restore manual binary rejected (not a PDF): manual=%s filename='%s' content_type='%s'",
            manual_id, file_name, file.content_type,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are allowed."
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The file is empty."
        )
    if len(data) > MAX_MANUAL_SIZE_BYTES:
        logger.warning(
            "Restore manual binary rejected (too large): manual=%s size=%d limit=%d",
            manual_id, len(data), MAX_MANUAL_SIZE_BYTES,
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The PDF exceeds the maximum allowed size of 4 MB."
        )

    try:
        manual.data = data
        manual.size_bytes = len(data)
        manual.content_type = "application/pdf"
        db.commit()
        logger.info(
            "Manual #%s binary restored (%d bytes) by %s",
            manual_id, len(data), current_user.username,
        )
        return {"success": True, "id": manual.id, "size_bytes": len(data)}
    except Exception:
        db.rollback()
        logger.exception("Error storing restored binary for manual #%s", manual_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error storing the restored PDF."
        )
