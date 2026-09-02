-- =============================================================================
-- Giaconi-Capra® PAS — Database Initialization Script (PostgreSQL)
-- Compatible con Vercel Postgres, Neon, Supabase, AWS RDS, PostgreSQL Local
-- =============================================================================

-- 1. Tabla de Solicitudes de Contacto y Cotizaciones (Leads)
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
    status VARCHAR(20) DEFAULT 'nuevo', -- 'nuevo', 'contactado', 'en_gestion', 'cerrado'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contact_leads_created_at ON contact_leads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_leads_status ON contact_leads (status);
CREATE INDEX IF NOT EXISTS idx_contact_leads_producto ON contact_leads (producto);

-- 2. Tabla de Opiniones / Testimonios de Clientes (Reviews)
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

-- 3. Tabla de Usuarios Administradores (Admin Users)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'admin', -- 'superadmin', 'admin'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users (username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);
