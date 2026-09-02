import sys
import os

# Asegurar que el path incluya la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database import engine, Base, SessionLocal
from api.models import ContactLead, Review
from sqlalchemy import select

def setup_database():
    print("=" * 60)
    print("Iniciando configuración de Base de Datos para Giaconi-Capra® PAS")
    print(f"URL: {engine.url}")
    print("=" * 60)

    # 1. Crear tablas
    print("-> Creando tablas (contact_leads, reviews)...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas o verificadas con éxito.")

    # 2. Cargar datos iniciales de prueba (Seed data)
    db = SessionLocal()
    try:
        existing_reviews = db.query(Review).count()
        if existing_reviews == 0:
            print("-> Insertando testimonios iniciales...")
            seed_reviews = [
                Review(
                    name="Carlos Mendoza",
                    role="Cliente Asegurado - Auto y Hogar",
                    avatar="CM",
                    rating=5,
                    text="Excelente atención de Leandro y Paola. Cuando tuve un siniestro con el vehículo gestionaron todo de inmediato sin vueltas. Es fundamental tener un asesor que te responda cuando realmente lo necesitás.",
                    is_approved=True
                ),
                Review(
                    name="Sofia Giannini",
                    role="Socia Directora - Comercio Pyme",
                    avatar="SG",
                    rating=5,
                    text="Revisaron los seguros que teníamos en nuestra empresa y nos bajaron los costos mejorando la cobertura de ART y Flotas. Transparencia total desde la primera reunión.",
                    is_approved=True
                ),
                Review(
                    name="Martín Rodríguez",
                    role="Inquilino - Caución para Alquiler",
                    avatar="MR",
                    rating=5,
                    text="Necesitaba una garantía de alquiler urgente y Paola me guió paso a paso para gestionarla en 24 horas. Súper profesional y con la mejor predisposición.",
                    is_approved=True
                )
            ]
            db.add_all(seed_reviews)
            db.commit()
            print(f"✓ Se insertaron {len(seed_reviews)} testimonios iniciales.")
        else:
            print(f"✓ La tabla 'reviews' ya contiene {existing_reviews} registros. No se requirió carga inicial.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed de datos: {e}")
        raise e
    finally:
        db.close()

    print("=" * 60)
    print("✓ Configuración de base de datos finalizada exitosamente.")
    print("=" * 60)

if __name__ == "__main__":
    setup_database()
