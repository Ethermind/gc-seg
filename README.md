# Giaconi-Capra® PAS — Landing Page & Cotizador Web Fullstack

Sitio web corporativo y cotizador de seguros para **Giaconi-Capra® Productores Asesores de Seguros**. Diseñado para ofrecer una experiencia moderna, accesible y optimizada en la conversión de clientes para coberturas individuales y corporativas, respaldado por un backend serverless en **FastAPI (Python)**, persistencia flexible (**PostgreSQL / SQLite**) y un **Panel de Administración (CRUD)** integrado.

---

## 🚀 Características Principales

* **Diseño Responsive & UI Moderna:** Interfaz pulida construida con Tailwind CSS, adaptada a dispositivos móviles, tablets y escritorio.
* **Catálogo Interactivo de Coberturas:** Navegación por pestañas (Personas / Empresas) y modales informativos con descarga de documentación en PDF.
* **Formulario de Contacto & Cotizador:** Validaciones en tiempo real (formato de email, sanitización de teléfono, límite de caracteres, aceptación de la Ley 25.326).
* **Seguridad con Google reCAPTCHA v2:** Verificación criptográfica en backend contra bots y spam en el formulario de cotización y en el modal de opiniones públicas (con bypass seguro para desarrollo/localhost).
* **Carrusel de Testimonios Dinámico:** Slider interactivo conectado al backend para lectura y publicación de opiniones de clientes reales.
* **Panel de Administración (`admin.html`):** Dashboard interactivo para gestión CRUD de solicitudes de cotización (`contact_leads`) y moderación/creación de opiniones (`reviews`), con enlace directo a WhatsApp.
* **Persistencia Dual (SQLite / PostgreSQL):** Conexión transparente mediante SQLAlchemy; usá `local.db` en local sin instalar servidores o conectate a PostgreSQL en producción (Vercel Postgres, Neon, Supabase).
* **Arquitectura Serverless para Vercel:** Frontend desacoplado con Serverless Functions en Python y pool de conexiones optimizado.
* **Integración con WhatsApp:** Botón flotante omnipresente y opción de contacto prioritario vía chat.
* **Normativa SSN & Legal:** Estructura preparada para el cumplimiento de la Superintendencia de Seguros de la Nación Argentina.

---

## 🛠️ Tecnologías Utilizadas

### Frontend
* **HTML5 Semantic Structure**
* **Tailwind CSS v3** (vía CDN / Configuración personalizada de marcas y colores)
* **Alpine.js v3** + `@alpinejs/collapse` (Gestión de estado reactivo y animaciones)
* **Lucide Icons** (Iconografía vectorial)
* **Google Fonts** (Tipografía *Plus Jakarta Sans*)
* **Google reCAPTCHA v2** (Widget de seguridad)

### Backend & Persistencia
* **Python 3.12+ / FastAPI** (Endpoints REST asíncronos y documentación automática OpenAPI)
* **SQLAlchemy 2.0 & Pydantic v2** (ORM, validación y sanitización de esquemas)
* **PostgreSQL / SQLite** (Compatible con Vercel Postgres, Neon, Supabase y SQLite local)
* **HTTPX** (Cliente HTTP asíncrono para validación con API de Google)

---

## 📂 Estructura del Proyecto

```text
.
├── .vscode/
│   └── launch.json             # Configuración para depuración con F5 en VS Code
├── api/                        # Backend Serverless en FastAPI
│   ├── index.py                # Punto de entrada ASGI de la API
│   ├── config.py               # Configuración y carga de variables (.env.local / .env)
│   ├── database.py             # Engine SQLAlchemy y pool de conexiones
│   ├── models.py               # Modelos relacionales de Base de Datos
│   ├── schemas.py              # Esquemas de validación Pydantic
│   ├── auth.py                 # Seguridad PRO (bcrypt hashing, JWT tokens y middleware)
│   ├── routes/
│   │   ├── auth.py             # Login, setup inicial (/api/auth/*)
│   │   ├── contact.py          # POST /api/contact (Recepción de cotizaciones)
│   │   ├── reviews.py          # GET y POST /api/reviews (Opiniones públicas)
│   │   ├── admin.py            # Endpoints CRUD para Panel de Control (/api/admin/*)
│   │   └── health.py           # GET /api/health (Health check)
│   └── services/
│       └── recaptcha.py        # Servicio de validación contra Google reCAPTCHA
├── scripts/                    # Scripts de Base de Datos y Utilidades
│   ├── init_db.sql             # DDL SQL de tablas e índices
│   ├── seed_data.sql           # Testimonios iniciales
│   └── setup_db.py             # Script de inicialización automática en Python
├── img/                        # Recursos gráficos y logotipos de aseguradoras
├── index.html                  # Landing page conectada con backend
├── index.html.old              # Respaldo de la versión previa (mock en memoria)
├── admin.html                  # Panel de administración SPA (Auth + JWT + CRUD)
├── requirements.txt            # Dependencias Python para Vercel
├── vercel.json                 # Configuración de rutas y rewrites en Vercel
├── .env.example                # Plantilla de variables de entorno
└── README.md                   # Documentación del proyecto
```

---

## 🗄️ Esquema de Base de Datos

### 1. Tabla `contact_leads` (Solicitudes de Cotización)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `nombre` | `VARCHAR(100)` | Nombre y apellido |
| `telefono` | `VARCHAR(50)` | Teléfono / WhatsApp |
| `email` | `VARCHAR(255)` | Correo electrónico |
| `producto` | `VARCHAR(100)` | Cobertura de interés |
| `mensaje` | `TEXT` | Detalle o mensaje |
| `wsp_preferred` | `BOOLEAN` | Si prefiere contacto por WhatsApp |
| `aceptar_datos` | `BOOLEAN` | Consentimiento Ley 25.326 |
| `ip_address` | `VARCHAR(45)` | IP del cliente |
| `user_agent` | `TEXT` | Navegador/dispositivo |
| `status` | `VARCHAR(20)` | Estado (`nuevo`, `contactado`, `en_gestion`, `cerrado`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha y hora de creación |

### 2. Tabla `reviews` (Testimonios de Clientes)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `name` | `VARCHAR(100)` | Nombre del autor |
| `role` | `VARCHAR(100)` | Rol o cobertura |
| `avatar` | `VARCHAR(10)` | Iniciales del avatar (ej: `CM`) |
| `rating` | `SMALLINT` | Puntuación de 1 a 5 estrellas |
| `text` | `TEXT` | Texto de la opinión |
| `is_approved` | `BOOLEAN` | Bandera de moderación y visibilidad web |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de publicación |

### 3. Tabla `admin_users` (Usuarios Administradores)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `username` | `VARCHAR(50) UNIQUE` | Nombre de usuario único |
| `email` | `VARCHAR(255) UNIQUE` | Correo electrónico único |
| `hashed_password` | `VARCHAR(255)` | Hash criptográfico bcrypt (12 rounds) |
| `full_name` | `VARCHAR(100)` | Nombre y apellido completo |
| `role` | `VARCHAR(20)` | Rol (`superadmin`, `admin`) |
| `is_active` | `BOOLEAN` | Estado de la cuenta |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de registro |
| `last_login` | `TIMESTAMP WITH TIME ZONE` | Fecha del último inicio de sesión |

---

## ⚙️ Configuración de Variables de Entorno

Crear un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Contenido del archivo `.env`:

```ini
# Opción 1: Base local SQLite (ideal para desarrollo rápido sin servidor)
DATABASE_URL=sqlite:///./local.db

# Opción 2: Base PostgreSQL (Vercel Postgres, Neon, Supabase o local)
# DATABASE_URL=postgresql://usuario:password@localhost:5432/gc_seg_db

# Google reCAPTCHA v2 (Checkbox)
# Para desarrollo/localhost se incluyen las claves oficiales de prueba de Google.
# Para producción, obtené tus claves en: https://www.google.com/recaptcha/admin
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI

# Entorno: development | production
ENVIRONMENT=development

# Orígenes permitidos para CORS (opcional)
ALLOWED_ORIGINS=*
```

> [!NOTE]
> **Modo Desarrollo:** En `ENVIRONMENT=development`, si `RECAPTCHA_SECRET_KEY` no está configurada, el sistema activa automáticamente un modo de bypass seguro para facilitar pruebas locales sin requerir credenciales externas.

---

## 💻 Desarrollo Local (Conda en WSL / Linux)

### 1. Crear y activar el entorno Conda
```bash
# Crear el entorno con Python 3.12 (requerido por el runtime de Vercel)
conda create -n gc-seg python=3.12 -y

# Activar el entorno
conda activate gc-seg
```

### 2. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar `.env` e inicializar la Base de Datos
```bash
# Crear .env si no lo hiciste
cp .env.example .env

# Crear tablas y cargar testimonios iniciales
python scripts/setup_db.py
```

### 4. Ejecutar el proyecto

#### Opción A: Simulación completa de Vercel (Recomendada)
Emula el enrutador de Vercel y levanta tanto el frontend como el backend bajo un mismo puerto:
```bash
npx vercel dev
```
* **Landing Page:** [http://localhost:3000](http://localhost:3000)
* **Panel de Administración:** [http://localhost:3000/admin.html](http://localhost:3000/admin.html)

#### Opción B: Servidores separados
* **Backend FastAPI (Terminal 1):**
  ```bash
  conda activate gc-seg
  uvicorn api.index:app --reload --port 8000
  ```
  * *Swagger UI:* [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
* **Frontend Estático (Terminal 2):**
  ```bash
  conda activate gc-seg
  python -m http.server 3000
  ```
  * *Landing Page:* [http://localhost:3000](http://localhost:3000)
  * *Panel de Administración:* [http://localhost:3000/admin.html](http://localhost:3000/admin.html)

---

## 🛡️ Panel de Administración (`admin.html`)

El panel es una **SPA (Single-Page Application)** con autenticación JWT completa. Accediendo a `/admin.html`:

### Sistema de Autenticación PRO

**Primera vez (Bootstrap):** Si la tabla `admin_users` está vacía, el panel muestra automáticamente un formulario de **configuración inicial** para crear el primer administrador con rol `superadmin`.

**Sesiones posteriores:** Se presenta el formulario de **login seguro** (usuario/email + contraseña). El token JWT se guarda en `localStorage` y se valida automáticamente al recargar la página.

**Seguridad implementada:**
- 🔐 Contraseñas hasheadas con **bcrypt** (12 rounds de salting)
- 🎟️ Tokens **JWT** firmados (HS256), con expiración configurable (default: 8 horas)
- 🚫 Todos los endpoints de `/api/admin/*` requieren Bearer Token válido (HTTP 401 si falla)
- 🛡️ Salvaguardas: no se puede eliminar la propia cuenta ni el último administrador del sistema

### Funcionalidades del Dashboard

1. **Métricas en tiempo real:** Total de solicitudes, pendientes, opiniones, administradores y promedio de calificación.
2. **Gestor de Solicitudes (`contact_leads`):**
   * Búsqueda en tiempo real (por nombre, email, teléfono, cobertura o texto).
   * Filtro por estado: `Nuevo`, `Contactado`, `En Gestión`, `Cerrado`.
   * Cambio de estado inmediato desde la tabla.
   * Botón directo de **WhatsApp** 💬 que preconfigura el saludo con los datos del cliente.
   * Modal de detalle completo 👁️ (con IP, agente y fecha).
   * Eliminación con confirmación 🗑️.
3. **Gestor de Opiniones (`reviews`):**
   * Creación manual de nuevos testimonios (+ Nueva Opinión).
   * Edición de opiniones existentes (nombre, rol, estrellas, texto).
   * Interruptor de visibilidad (publicar u ocultar del carrusel web con un click).
   * Eliminación con confirmación 🗑️.
4. **Gestor de Administradores (`admin_users`):**
   * Listado de todos los usuarios con acceso al panel, su rol y último acceso.
   * Creación de nuevos administradores con rol `admin` o `superadmin`.
   * Cambio de contraseña (🔑) de cualquier usuario.
   * Eliminación de usuarios con salvaguardas de seguridad.

### Variables de Entorno para Producción (Auth)

```ini
JWT_SECRET_KEY=<clave-secreta-larga-y-aleatoria>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

> ⚠️ **Importante:** En producción, configurar `JWT_SECRET_KEY` con un valor largo y aleatorio en Vercel Dashboard (`npx vercel env add JWT_SECRET_KEY`). Nunca subir este valor a GitHub.

---

## 🐞 Depuración en Visual Studio Code

El repositorio incluye la configuración lista en `.vscode/launch.json` para depurar el backend con breakpoints:

1. **Seleccionar el intérprete:** Presioná `Ctrl + Shift + P` -> `Python: Select Interpreter` -> Seleccioná `gc-seg` (Conda).
2. **Colocar Breakpoints:** Abrí cualquier archivo de `api/` (ej. `api/routes/contact.py` o `api/routes/admin.py`) y hacé click junto al número de línea (punto rojo 🔴).
3. **Iniciar depuración:** Presioná `F5` (o pestaña *Run and Debug* ▶ **Python: FastAPI (Backend gc-seg)**).
4. El debugger se detendrá automáticamente en tus puntos de interrupción al recibir solicitudes desde el frontend o Swagger.

---

## 🚀 Despliegue en Vercel

1. **Importar el Repositorio en Vercel:**
   - Conectá tu cuenta de GitHub y seleccioná el repositorio `gc-seg`.
2. **Crear o Vincular Base de Datos PostgreSQL:**
   - En la pestaña **Storage** del proyecto en Vercel, creá una base de datos **Vercel Postgres** (o vinculá tu base de datos de **Neon** / **Supabase**).
   - Vercel inyectará automáticamente `POSTGRES_URL` (y `DATABASE_URL`).
3. **Ejecutar el Script DDL:**
   - En la consola SQL de Vercel Storage (o en tu cliente SQL / Neon Editor), ejecutá el contenido de:
     - `scripts/init_db.sql`
     - `scripts/seed_data.sql` (opcional, para cargar las reseñas iniciales)
4. **Configurar Variables de Entorno en Vercel:**
   - `RECAPTCHA_SECRET_KEY`: Tu clave secreta de Google reCAPTCHA.
   - `RECAPTCHA_SITE_KEY`: Tu clave pública de Google reCAPTCHA.
   - `JWT_SECRET_KEY`: Clave larga y aleatoria para firmar los tokens JWT del panel admin.
   - `ENVIRONMENT`: `production`
5. **Deploy:**
   - Hacé click en **Deploy**. Vercel compilará la Serverless Function en `/api/*` y servirá los archivos estáticos (`index.html`, `admin.html`, etc.) en la raíz.
6. **Primer Acceso al Panel:**
   - Abrí `https://tu-dominio.vercel.app/admin.html`. Si la tabla `admin_users` está vacía, el sistema te guiará para crear el primer administrador automáticamente.
