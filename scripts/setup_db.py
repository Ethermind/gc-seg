import sys
import os

# Asegurar que el path incluya la raiz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database import engine, Base, SessionLocal
from api.models import ContactLead, Review, Coverage, FAQ

def setup_database():
    print("=" * 60)
    print("Iniciando configuracion de Base de Datos para Giaconi-Capra® PAS")
    print(f"URL: {engine.url}")
    print("=" * 60)

    # 1. Crear tablas
    print("-> Creando tablas (contact_leads, reviews, coverages, faqs, admin_users, manuals)...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas o verificadas con exito.")

    # 2. Cargar datos iniciales de prueba (Seed data)
    db = SessionLocal()
    try:
        # Seed Reviews
        existing_reviews = db.query(Review).count()
        if existing_reviews == 0:
            print("-> Insertando testimonios iniciales...")
            seed_reviews = [
                Review(
                    name="Carlos Mendoza",
                    role="Cliente Asegurado - Auto y Hogar",
                    avatar="CM",
                    rating=5,
                    text="Excelente atencion de Leandro y Paola. Cuando tuve un siniestro con el vehiculo gestionaron todo de inmediato sin vueltas. Es fundamental tener un asesor que te responda cuando realmente lo necesitas.",
                    is_approved=True
                ),
                Review(
                    name="Sofia Giannini",
                    role="Socia Directora - Comercio Pyme",
                    avatar="SG",
                    rating=5,
                    text="Revisaron los seguros que teniamos en nuestra empresa y nos bajaron los costos mejorando la cobertura de ART y Flotas. Transparencia total desde la primera reunion.",
                    is_approved=True
                ),
                Review(
                    name="Martin Rodriguez",
                    role="Inquilino - Caucion para Alquiler",
                    avatar="MR",
                    rating=5,
                    text="Necesitaba una garantia de alquiler urgente y Paola me guio paso a paso para gestionarla en 24 horas. Super profesional y con la mejor predisposicion.",
                    is_approved=True
                )
            ]
            db.add_all(seed_reviews)
            db.commit()
            print(f"✓ Se insertaron {len(seed_reviews)} testimonios iniciales.")
        else:
            print(f"✓ La tabla 'reviews' ya contiene {existing_reviews} registros. No se requirio carga inicial.")

        # Seed Coverages (Personas)
        existing_coverages = db.query(Coverage).count()
        if existing_coverages == 0:
            print("-> Insertando coberturas iniciales...")
            seed_coverages = [
                # Personas
                Coverage(categoria="personas", titulo="Auto", icono="car", descripcion="Protege tu vehiculo frente a accidentes, robo, incendio y danos, con distintas alternativas de cobertura para elegir la que mejor se adapte a vos.", orden=1),
                Coverage(categoria="personas", titulo="Moto", icono="motorbike", descripcion="Coberturas para que disfrutes tu moto con mayor tranquilidad, protegiendote frente a responsabilidad civil, robo, incendio y otros imprevistos.", orden=2),
                Coverage(categoria="personas", titulo="Hogar", icono="home", descripcion="Protege tu casa y todo lo que hay en ella frente a incendio, robo, danos y otros imprevistos que pueden afectar tu patrimonio.", orden=3),
                Coverage(categoria="personas", titulo="Vida", icono="heart-pulse", descripcion="Una forma de cuidar economicamente a quienes mas queres. Brinda respaldo ante situaciones inesperadas y ayuda a proteger la estabilidad de tu familia.", orden=4),
                Coverage(categoria="personas", titulo="Retiro", icono="trending-up", descripcion="Empeza hoy a construir el capital que queres disfrutar manana. Un plan de ahorro a largo plazo pensado para complementar tus ingresos futuros.", orden=5),
                Coverage(categoria="personas", titulo="Accidentes Personales", icono="activity", descripcion="Protegete vos o protege a quienes realizan trabajos para vos frente a las consecuencias de un accidente.", orden=6),
                Coverage(categoria="personas", titulo="Viajes", icono="plane", descripcion="Viajá con respaldo ante imprevistos lejos de casa, con asistencia frente a emergencias medicas y otras situaciones.", orden=7),
                Coverage(categoria="personas", titulo="Bicicletas y Ecomovilidad", icono="bike", descripcion="Protege tu bicicleta, monopatin electrico y otros medios de movilidad personal frente a robo e imprevistos, incluyendo Responsabilidad Civil.", orden=8),
                Coverage(categoria="personas", titulo="Celulares y Portatiles", icono="smartphone", descripcion="Protege los dispositivos que te acompanan todos los dias, como celulares, notebooks y tablets, frente a robo y otros imprevistos.", orden=9),
                Coverage(categoria="personas", titulo="Caucion para Alquileres", icono="key-round", descripcion="El seguro de caucion puede reemplazar la garantia propietaria y brindar al propietario el respaldo necesario.", orden=10),
                # Empresas
                Coverage(categoria="empresas", titulo="Comercio", icono="store", descripcion="Protege tu negocio, mercaderia, instalaciones y equipamiento frente a los principales imprevistos.", orden=1),
                Coverage(categoria="empresas", titulo="Consorcio", icono="building", descripcion="Protege el edificio, sus espacios comunes y la responsabilidad del consorcio frente a los principales riesgos e imprevistos.", orden=2),
                Coverage(categoria="empresas", titulo="Responsabilidad Civil", icono="scale", descripcion="Protege tu patrimonio frente a reclamos por danos que, como consecuencia de tu actividad, puedas ocasionar a terceros.", orden=3),
                Coverage(categoria="empresas", titulo="ART", icono="hard-hat", badge="Nuevo", descripcion="Proteccion para tus empleados frente a accidentes de trabajo y enfermedades profesionales, cumpliendo con la normativa vigente.", orden=4),
                Coverage(categoria="empresas", titulo="Caucion Empresas", icono="file-text", descripcion="Una alternativa para garantizar el cumplimiento de distintas obligaciones sin inmovilizar capital.", orden=5),
                Coverage(categoria="empresas", titulo="Transporte", icono="truck", descripcion="Protege las mercaderias durante su traslado frente a perdidas o danos que puedan ocurrir en el camino.", orden=6),
                Coverage(categoria="empresas", titulo="Equipos y Maquinarias", icono="wrench", descripcion="Protege las herramientas, maquinarias y equipos esenciales para desarrollar tu actividad frente a distintos danos.", orden=7),
                Coverage(categoria="empresas", titulo="Flotas", icono="car-front", descripcion="Protege todos los vehiculos de tu empresa bajo una cobertura pensada para simplificar su administracion.", orden=8),
                Coverage(categoria="empresas", titulo="Retiro para Empleados", icono="award", badge="Nuevo", descripcion="Ofrece a tus colaboradores un beneficio pensado para su futuro, ayudandolos a construir un ahorro para complementar su jubilacion.", orden=9),
            ]
            db.add_all(seed_coverages)
            db.commit()
            print(f"✓ Se insertaron {len(seed_coverages)} coberturas iniciales.")
        else:
            print(f"✓ La tabla 'coverages' ya contiene {existing_coverages} registros. No se requirio carga inicial.")

        # Seed FAQs
        existing_faqs = db.query(FAQ).count()
        if existing_faqs == 0:
            print("-> Insertando FAQs iniciales...")
            seed_faqs = [
                FAQ(pregunta="Por que contratar mi seguro a traves de un Productor Asesor de Seguros?", respuesta="Porque no solo te ayudamos a contratar una poliza. Analizamos distintas alternativas, te explicamos que estas cubriendo y te acompanamos durante la vigencia del seguro y, especialmente, cuando ocurre un siniestro.", categoria="general", orden=1),
                FAQ(pregunta="Trabajan con una sola compania de seguros?", respuesta="No. Trabajamos con distintas companias aseguradoras, lo que nos permite evaluar alternativas y buscar la cobertura que mejor se adapte a tus necesidades.", categoria="general", orden=2),
                FAQ(pregunta="Tiene algun costo adicional contratar el seguro con ustedes?", respuesta="No. Nuestro asesoramiento como Productores Asesores de Seguros no representa un costo adicional para vos sobre el precio de la poliza.", categoria="general", orden=3),
                FAQ(pregunta="Puedo pedir una cotizacion sin compromiso?", respuesta="Si. Contanos que necesitás asegurar y analizamos las alternativas disponibles para ofrecerte una propuesta acorde a tus necesidades.", categoria="cotizacion", orden=4),
                FAQ(pregunta="Que tengo que hacer si tengo un siniestro?", respuesta="Contactanos lo antes posible. Te vamos a indicar que documentacion necesitas, como realizar la denuncia y te acompanaremos durante la gestion del siniestro ante la compania.", categoria="siniestros", orden=5),
                FAQ(pregunta="Puedo cambiar de compania si ya tengo un seguro contratado?", respuesta="Si. Podemos revisar tu cobertura actual y evaluar otras alternativas. Antes de realizar cualquier cambio, verificamos fechas, condiciones y coberturas para evitar que quedes sin proteccion.", categoria="general", orden=6),
                FAQ(pregunta="Puedo contratar un seguro completamente online?", respuesta="En muchos casos, si. Podemos realizar la cotizacion, solicitar la documentacion y gestionar la emision de manera digital, manteniendo siempre el asesoramiento personalizado.", categoria="cotizacion", orden=7),
                FAQ(pregunta="Que informacion necesito para pedir una cotizacion?", respuesta="Depende del seguro que necesites. Con algunos datos basicos podemos comenzar y despues te indicaremos especificamente que documentacion necesitamos para avanzar.", categoria="cotizacion", orden=8),
                FAQ(pregunta="Tambien trabajan con empresas y comercios?", respuesta="Si. Asesoramos a comercios, profesionales, consorcios y empresas, desde coberturas especificas hasta programas integrales que contemplen distintos riesgos de la actividad.", categoria="empresas", orden=9),
                FAQ(pregunta="Como se si las coberturas que tengo actualmente son suficientes?", respuesta="Podemos revisar tus polizas actuales, analizar sumas aseguradas, coberturas y necesidades reales, y ayudarte a detectar posibles faltantes o coberturas que convenga actualizar.", categoria="general", orden=10),
                FAQ(pregunta="Despues de contratar, con quien me comunico si necesito algo?", respuesta="Con nosotros. Queremos que tengas siempre a quien recurrir. Desde una modificacion en tu poliza hasta un siniestro o una consulta sobre tu cobertura, nuestro trabajo es acompanarte tambien despues de la contratacion.", categoria="general", orden=11),
            ]
            db.add_all(seed_faqs)
            db.commit()
            print(f"✓ Se insertaron {len(seed_faqs)} FAQs iniciales.")
        else:
            print(f"✓ La tabla 'faqs' ya contiene {existing_faqs} registros. No se requirio carga inicial.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed de datos: {e}")
        raise e
    finally:
        db.close()

    print("=" * 60)
    print("✓ Configuracion de base de datos finalizada exitosamente.")
    print("=" * 60)

if __name__ == "__main__":
    setup_database()
