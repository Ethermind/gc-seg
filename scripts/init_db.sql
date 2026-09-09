-- =============================================================================
-- Giaconi-Capra® PAS — Database Initialization & Optimization Script (PostgreSQL)
-- Compatible con Vercel Postgres, Neon, Supabase, AWS RDS, PostgreSQL Local (13+)
-- Idempotente: seguro de ejecutar múltiples veces sin borrar ni duplicar datos.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Tabla de Solicitudes de Contacto y Cotizaciones (Leads)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_leads (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    producto VARCHAR(100),
    mensaje TEXT,
    wsp_preferred BOOLEAN DEFAULT FALSE,
    aceptar_datos BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'nuevo' CHECK (status IN ('nuevo', 'contactado', 'en_gestion', 'cerrado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contact_leads_created_at ON contact_leads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_leads_status ON contact_leads (status);
CREATE INDEX IF NOT EXISTS idx_contact_leads_producto ON contact_leads (producto);

-- -----------------------------------------------------------------------------
-- 2. Tabla de Opiniones / Testimonios de Clientes (Reviews)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) DEFAULT 'Cliente Asegurado',
    avatar VARCHAR(10) NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    text TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reviews_approved_created ON reviews (is_approved, created_at DESC);

-- -----------------------------------------------------------------------------
-- 3. Tabla de Usuarios Administradores (Admin Users)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'admin' CHECK (role IN ('superadmin', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users (username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);

-- -----------------------------------------------------------------------------
-- 4. Tabla de Manuales de Producto (PDF almacenados como binarios en DB)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS manuals (
    id SERIAL PRIMARY KEY,
    producto VARCHAR(100) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'application/pdf',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    data BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_manuals_producto ON manuals (producto);

-- -----------------------------------------------------------------------------
-- 5. Tabla de Coberturas (Personas / Empresas)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coverages (
    id SERIAL PRIMARY KEY,
    categoria VARCHAR(20) NOT NULL CHECK (categoria IN ('personas', 'empresas')),
    titulo VARCHAR(100) NOT NULL,
    icono VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    badge VARCHAR(20),
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_coverages_categoria_titulo UNIQUE (categoria, titulo)
);

CREATE INDEX IF NOT EXISTS idx_coverages_cat_activo_orden ON coverages (categoria, activo, orden ASC);

-- -----------------------------------------------------------------------------
-- 6. Tabla de Preguntas Frecuentes (FAQs)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    categoria VARCHAR(50),
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_faqs_pregunta UNIQUE (pregunta)
);

CREATE INDEX IF NOT EXISTS idx_faqs_activo_orden ON faqs (activo, orden ASC);


-- =============================================================================
-- SEED DATA INICIAL (IDEMPOTENTE CON ON CONFLICT DO NOTHING)
-- =============================================================================

-- A. Testimonios iniciales
INSERT INTO reviews (name, role, avatar, rating, text, is_approved)
VALUES
    (
        'Carlos Mendoza',
        'Cliente Asegurado - Auto y Hogar',
        'CM',
        5,
        'Excelente atención de Leandro y Paola. Cuando tuve un siniestro con el vehículo gestionaron todo de inmediato sin vueltas. Es fundamental tener un asesor que te responda cuando realmente lo necesitás.',
        TRUE
    ),
    (
        'Sofia Giannini',
        'Socia Directora - Comercio Pyme',
        'SG',
        5,
        'Revisaron los seguros que teníamos en nuestra empresa y nos bajaron los costos mejorando la cobertura de ART y Flotas. Transparencia total desde la primera reunión.',
        TRUE
    ),
    (
        'Martín Rodríguez',
        'Inquilino - Caución para Alquiler',
        'MR',
        5,
        'Necesitaba una garantía de alquiler urgente y Paola me guió paso a paso para gestionarla en 24 horas. Súper profesional y con la mejor predisposición.',
        TRUE
    )
ON CONFLICT DO NOTHING;

-- B. Coberturas iniciales (Personas y Empresas)
INSERT INTO coverages (categoria, titulo, icono, descripcion, badge, orden, activo)
VALUES
    -- Personas
    ('personas', 'Auto', 'car', 'Protegé tu vehículo frente a accidentes, robo, incendio y daños, con distintas alternativas de cobertura para elegir la que mejor se adapte a vos.', NULL, 1, TRUE),
    ('personas', 'Moto', 'motorbike', 'Coberturas para que disfrutes tu moto con mayor tranquilidad, protegiéndote frente a responsabilidad civil, robo, incendio y otros imprevistos.', NULL, 2, TRUE),
    ('personas', 'Hogar', 'home', 'Protegé tu casa y todo lo que hay en ella frente a incendio, robo, daños y otros imprevistos que pueden afectar tu patrimonio.', NULL, 3, TRUE),
    ('personas', 'Vida', 'heart-pulse', 'Una forma de cuidar económicamente a quienes más querés. Brinda respaldo ante situaciones inesperadas y ayuda a proteger la estabilidad de tu familia.', NULL, 4, TRUE),
    ('personas', 'Retiro', 'trending-up', 'Empezá hoy a construir el capital que querés disfrutar mañana. Un plan de ahorro a largo plazo pensado para complementar tus ingresos futuros.', NULL, 5, TRUE),
    ('personas', 'Accidentes Personales', 'activity', 'Protegete vos o protegé a quienes realizan trabajos para vos frente a las consecuencias de un accidente.', NULL, 6, TRUE),
    ('personas', 'Viajes', 'plane', 'Viajá con respaldo ante imprevistos lejos de casa, con asistencia frente a emergencias médicas y otras situaciones.', NULL, 7, TRUE),
    ('personas', 'Bicicletas y Ecomovilidad', 'bike', 'Protegé tu bicicleta, monopatín eléctrico y otros medios de movilidad personal frente a robo e imprevistos, incluyendo Responsabilidad Civil.', NULL, 8, TRUE),
    ('personas', 'Celulares y Portátiles', 'smartphone', 'Protegé los dispositivos que te acompañan todos los días, como celulares, notebooks y tablets, frente a robo y otros imprevistos.', NULL, 9, TRUE),
    ('personas', 'Caución para Alquileres', 'key-round', 'El seguro de caución puede reemplazar la garantía propietaria y brindar al propietario el respaldo necesario.', NULL, 10, TRUE),

    -- Empresas
    ('empresas', 'Comercio', 'store', 'Protegé tu negocio, mercadería, instalaciones y equipamiento frente a los principales imprevistos.', NULL, 1, TRUE),
    ('empresas', 'Consorcio', 'building', 'Protegé el edificio, sus espacios comunes y la responsabilidad del consorcio frente a los principales riesgos e imprevistos.', NULL, 2, TRUE),
    ('empresas', 'Responsabilidad Civil', 'scale', 'Protegé tu patrimonio frente a reclamos por daños que, como consecuencia de tu actividad, puedas ocasionar a terceros.', NULL, 3, TRUE),
    ('empresas', 'ART', 'hard-hat', 'Protección para tus empleados frente a accidentes de trabajo y enfermedades profesionales, cumpliendo con la normativa vigente.', 'Nuevo', 4, TRUE),
    ('empresas', 'Caución Empresas', 'file-text', 'Una alternativa para garantizar el cumplimiento de distintas obligaciones sin inmovilizar capital.', NULL, 5, TRUE),
    ('empresas', 'Transporte', 'truck', 'Protegé las mercaderías durante su traslado frente a pérdidas o daños que puedan ocurrir en el camino.', NULL, 6, TRUE),
    ('empresas', 'Equipos y Maquinarias', 'wrench', 'Protegé las herramientas, maquinarias y equipos esenciales para desarrollar tu actividad frente a distintos daños.', NULL, 7, TRUE),
    ('empresas', 'Flotas', 'car-front', 'Protegé todos los vehículos de tu empresa bajo una cobertura pensada para simplificar su administración.', NULL, 8, TRUE),
    ('empresas', 'Retiro para Empleados', 'award', 'Ofrecé a tus colaboradores un beneficio pensado para su futuro, ayudándolos a construir un ahorro para complementar su jubilación.', 'Nuevo', 9, TRUE)
ON CONFLICT (categoria, titulo) DO NOTHING;

-- C. Preguntas Frecuentes iniciales (FAQs)
INSERT INTO faqs (pregunta, respuesta, categoria, orden, activo)
VALUES
    ('¿Por qué contratar mi seguro a través de un Productor Asesor de Seguros?', 'Porque no solo te ayudamos a contratar una póliza. Analizamos distintas alternativas, te explicamos qué estás cubriendo y te acompañamos durante la vigencia del seguro y, especialmente, cuando ocurre un siniestro.', 'general', 1, TRUE),
    ('¿Trabajan con una sola compañía de seguros?', 'No. Trabajamos con distintas compañías aseguradoras, lo que nos permite evaluar alternativas y buscar la cobertura que mejor se adapte a tus necesidades.', 'general', 2, TRUE),
    ('¿Tiene algún costo adicional contratar el seguro con ustedes?', 'No. Nuestro asesoramiento como Productores Asesores de Seguros no representa un costo adicional para vos sobre el precio de la póliza.', 'general', 3, TRUE),
    ('¿Puedo pedir una cotización sin compromiso?', 'Sí. Contanos qué necesitás asegurar y analizamos las alternativas disponibles para ofrecerte una propuesta acorde a tus necesidades.', 'cotizacion', 4, TRUE),
    ('¿Qué tengo que hacer si tengo un siniestro?', 'Contactanos lo antes posible. Te vamos a indicar qué documentación necesitás, cómo realizar la denuncia y te acompañaremos durante la gestión del siniestro ante la compañía.', 'siniestros', 5, TRUE),
    ('¿Puedo cambiar de compañía si ya tengo un seguro contratado?', 'Sí. Podemos revisar tu cobertura actual y evaluar otras alternativas. Antes de realizar cualquier cambio, verificamos fechas, condiciones y coberturas para evitar que quedes sin protección.', 'general', 6, TRUE),
    ('¿Puedo contratar un seguro completamente online?', 'En muchos casos, sí. Podemos realizar la cotización, solicitar la documentación y gestionar la emisión de manera digital, manteniendo siempre el asesoramiento personalizado.', 'cotizacion', 7, TRUE),
    ('¿Qué información necesito para pedir una cotización?', 'Depende del seguro que necesites. Con algunos datos básicos podemos comenzar y después te indicaremos específicamente qué documentación necesitamos para avanzar.', 'cotizacion', 8, TRUE),
    ('¿También trabajan con empresas y comercios?', 'Sí. Asesoramos a comercios, profesionales, consorcios y empresas, desde coberturas específicas hasta programas integrales que contemplen distintos riesgos de la actividad.', 'empresas', 9, TRUE),
    ('¿Cómo sé si las coberturas que tengo actualmente son suficientes?', 'Podemos revisar tus pólizas actuales, analizar sumas aseguradas, coberturas y necesidades reales, y ayudarte a detectar posibles faltantes o coberturas que convenga actualizar.', 'general', 10, TRUE),
    ('¿Después de contratar, con quién me comunico si necesito algo?', 'Con nosotros. Queremos que tengas siempre a quién recurrir. Desde una modificación en tu póliza hasta un siniestro o una consulta sobre tu cobertura, nuestro trabajo es acompañarte también después de la contratación.', 'general', 11, TRUE)
ON CONFLICT (pregunta) DO NOTHING;
