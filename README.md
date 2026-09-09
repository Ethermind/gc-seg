# Giaconi-Capra® PAS — Website & Insurance Quote Manager

Sitio web corporativo y plataforma integral de cotizaciones para **Giaconi-Capra® Productores Asesores de Seguros**. Desarrollado con frontend estático reactivo (Tailwind CSS + Alpine.js) conectado a una **API Serverless FastAPI (Python)**, persistencia flexible (**SQLite en local / PostgreSQL en producción**) y un **Panel de Administración (CRUD)** completo.

---

## 🚦 Estado del Proyecto

| Archivo | Rol | Descripción |
| :--- | :--- | :--- |
| `index.html` | **Producción (MVP)** | Landing page principal conectada al backend (`/api/contact`, `/api/reviews`, `/api/coverages`, `/api/faqs`, `/api/manuals`). Cuenta con Turnstile invisible y datos 100% dinámicos desde la base de datos. |
| `index-OLD.html` | **Backup / Histórico** | Copia de respaldo de la versión previa estática / POC. |
| `admin.html` | **Panel de Administración** | SPA administrativa completa con autenticación JWT, métricas en tiempo real y CRUD para leads, testimonios, coberturas, FAQs, manuales PDF y administradores. |

---

## 🚀 Características Principales

* **Interfaz Responsiva & Moderna:** Diseñada con Tailwind CSS y tipografía *Plus Jakarta Sans*, adaptada a móviles, tablets y monitores de escritorio.
* **Catálogo Dinámico de Coberturas:** Pestañas separadas para *Personas* y *Empresas*. Se gestionan (título, descripción, icono Lucide, badge y orden) desde el panel de administración y se reflejan en tiempo real en la web.
* **Formulario de Contacto y Cotizaciones:** Validación en tiempo real (formato de correo, sanitización de teléfonos, longitud de mensajes, consentimiento de Ley 25.326). El listado de coberturas se sincroniza dinámicamente con la base de datos.
* **Preguntas Frecuentes (FAQs) Dinámicas:** Acordeón interactivo cuyas preguntas, respuestas, categorías y orden se cargan desde la API y se administran desde el panel.
* **Cloudflare Turnstile (Invisible):** Verificación anti-bots sin captchas ni checkboxes molestos ("No soy un robot" eliminado). Protege tanto el envío de cotizaciones como las opiniones de clientes.
* **Rate Limiting por IP (`slowapi`):** Límite configurado a 10 peticiones/minuto por IP en los endpoints públicos de cotización y opiniones (`/api/contact` y `/api/reviews`).
* **Carrusel Dinámico de Testimonios:** Lee reseñas aprobadas desde el backend y permite a clientes publicar opiniones con calificación por estrellas (1 a 5).
* **Gestor de Manuales PDF por Producto:** Carga de manuales en PDF desde el panel (almacenados como blobs en base de datos). Los manuales se vinculan automáticamente con la cobertura seleccionada y se listan en el modal de detalle.
* **Panel de Control Administrativo (`admin.html`):**
  - Métricas en vivo (solicitudes totales, nuevas, opiniones, administradores).
  - Gestión de Cotizaciones (cambio de estado, filtros, detalle con IP/dispositivo, botón directo a WhatsApp).
  - Moderación de Opiniones (crear, editar, aprobar/ocultar y eliminar).
  - Gestión de Coberturas (Personas y Empresas).
  - Gestión de Preguntas Frecuentes (FAQs).
  - Gestor de Manuales PDF (asociación dinámica a coberturas).
  - Gestión de Usuarios Administradores (roles `admin` y `superadmin`, reseteo de contraseñas, protecciones contra eliminación propia o del último superadmin).
* **Persistencia Dual (SQLite / PostgreSQL):** Conexión transparente mediante SQLAlchemy 2.0 (SQLite local y PostgreSQL para Vercel/Neon/Supabase).
* **Arquitectura Serverless optimizada para Vercel:** Handlers ASGI desacoplados, pool de conexiones reciclable y migración DDL automática en cold start (`init_db()`).

---

## 🛠️ Stack Tecnológico

### Frontend
* **HTML5 Semántico**
* **Tailwind CSS v3** (CDN con configuración de paleta de marca)
* **Alpine.js v3** + `@alpinejs/collapse`
* **Lucide Icons**
* **Cloudflare Turnstile** (JavaScript API invisible)
* **Google Fonts** (Plus Jakarta Sans)

### Backend & Persistencia
* **Python 3.12+ / FastAPI** (REST endpoints y documentación Swagger/OpenAPI)
* **SQLAlchemy 2.0 & Pydantic v2** (ORM, validación estricta y sanitización)
* **SlowAPI** (Rate Limiter con mitigación de spam por IP)
* **PostgreSQL / SQLite** (PostgreSQL en Vercel/Neon/Supabase, SQLite local)
* **HTTPX** (Cliente asíncrono para verificar tokens de Turnstile ante Cloudflare)
* **PyJWT + bcrypt** (Autenticación y hashing seguro de contraseñas)

---

## 📂 Estructura del Repositorio

```text
.
├── .vscode/
│   └── launch.json             # Configuración de depuración con F5 en VS Code
├── api/                        # Backend Serverless FastAPI
│   ├── index.py                # ASGI entrypoint + exception handlers
│   ├── config.py               # Carga de variables de entorno y settings
│   ├── database.py             # Engine SQLAlchemy y pool de conexiones
│   ├── models.py               # Modelos relacionales ORM (6 entidades)
│   ├── schemas.py              # Esquemas Pydantic para request/response
│   ├── auth.py                 # Hashing bcrypt, JWT tokens y middleware
│   ├── ratelimit.py            # Instancia Limiter de slowapi por IP
│   ├── routes/
│   │   ├── auth.py             # Autenticación y bootstrap (/api/auth/*)
│   │   ├── contact.py          # Cotizaciones públicas (/api/contact)
│   │   ├── reviews.py          # Testimonios públicos (/api/reviews)
│   │   ├── coverages.py        # Coberturas públicas y admin (/api/coverages)
│   │   ├── faqs.py             # Preguntas frecuentes públicas y admin (/api/faqs)
│   │   ├── manuals.py          # Manuales públicos y descargas (/api/manuals)
│   │   ├── admin.py            # Dashboard admin (/api/admin/*)
│   │   └── health.py           # Health check (/api/health)
│   └── services/
│       └── turnstile.py        # Servicio de verificación Cloudflare Turnstile
├── scripts/                    # Scripts de base de datos
│   ├── init_db.sql             # DDL completo con índices optimizados
│   ├── seed_data.sql           # Testimonios iniciales en SQL
│   └── setup_db.py             # Script Python para creación y seed inicial
├── img/                        # Recursos gráficos y logotipos
├── index.html                  # Landing page principal (MVP productivo conectado a API)
├── index-OLD.html              # Copia de respaldo histórica
├── admin.html                  # Panel de administración SPA (JWT + 6 tabs)
├── requirements.txt            # Dependencias de Python
├── vercel.json                 # Configuración de routing y rewrites en Vercel
├── .env.example                # Plantilla de variables de entorno
└── README.md                   # Esta documentación
```

---

## 🗄️ Esquema de Base de Datos

### 1. `contact_leads` (Solicitudes de Cotización)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `nombre` | `VARCHAR(100)` | Nombre completo |
| `telefono` | `VARCHAR(50)` | Teléfono / WhatsApp |
| `email` | `VARCHAR(255)` | Correo electrónico |
| `producto` | `VARCHAR(100)` | Cobertura solicitada |
| `mensaje` | `TEXT` | Mensaje o detalle |
| `wsp_preferred` | `BOOLEAN` | Preferencia de contacto por WhatsApp |
| `aceptar_datos` | `BOOLEAN` | Aceptación Ley 25.326 |
| `ip_address` | `VARCHAR(45)` | Dirección IP del cliente |
| `user_agent` | `TEXT` | Dispositivo y navegador |
| `status` | `VARCHAR(20)` | Estado (`nuevo`, `contactado`, `en_gestion`, `cerrado`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha y hora de creación |

### 2. `reviews` (Testimonios y Opiniones)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `name` | `VARCHAR(100)` | Nombre del autor |
| `role` | `VARCHAR(100)` | Rol o producto contratado |
| `avatar` | `VARCHAR(10)` | Iniciales del avatar (ej: `CM`) |
| `rating` | `SMALLINT` | Puntuación de 1 a 5 estrellas |
| `text` | `TEXT` | Mensaje de la opinión |
| `is_approved` | `BOOLEAN` | Visibilidad pública en la web |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de publicación |

### 3. `admin_users` (Usuarios Administradores)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `username` | `VARCHAR(50) UNIQUE` | Nombre de usuario |
| `email` | `VARCHAR(255) UNIQUE` | Correo electrónico |
| `hashed_password` | `VARCHAR(255)` | Hash bcrypt (12 rondas) |
| `full_name` | `VARCHAR(100)` | Nombre y apellido |
| `role` | `VARCHAR(20)` | Rol (`superadmin`, `admin`) |
| `is_active` | `BOOLEAN` | Estado de la cuenta |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de alta |
| `last_login` | `TIMESTAMP WITH TIME ZONE` | Último inicio de sesión |

### 4. `manuals` (Manuales y Documentación PDF)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `producto` | `VARCHAR(100)` | Cobertura asociada |
| `titulo` | `VARCHAR(150)` | Título descriptivo |
| `file_name` | `VARCHAR(255)` | Nombre original del archivo |
| `content_type` | `VARCHAR(50)` | MIME type (`application/pdf`) |
| `size_bytes` | `INTEGER` | Tamaño en bytes (máx 4 MB) |
| `data` | `BYTEA` / `BLOB` | Contenido binario del PDF (carga diferida) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de subida |

### 5. `coverages` (Coberturas de Personas y Empresas)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `categoria` | `VARCHAR(20)` | `personas` o `empresas` |
| `titulo` | `VARCHAR(100)` | Nombre de la cobertura (ej: Auto, ART) |
| `icono` | `VARCHAR(50)` | Nombre del icono Lucide (ej: `car`, `store`) |
| `descripcion` | `TEXT` | Descripción completa de la póliza |
| `badge` | `VARCHAR(20)` | Etiqueta opcional (ej: `Nuevo`) |
| `orden` | `INTEGER` | Posición de visualización |
| `activo` | `BOOLEAN` | Visible o pausada en la web |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de creación |

### 6. `faqs` (Preguntas Frecuentes)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `pregunta` | `TEXT` | Pregunta planteada |
| `respuesta` | `TEXT` | Respuesta detallada |
| `categoria` | `VARCHAR(50)` | Agrupador (ej: `general`, `cotizacion`) |
| `orden` | `INTEGER` | Orden en el acordeón |
| `activo` | `BOOLEAN` | Visible o inactiva |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Fecha de creación |

---

## ⚙️ Variables de Entorno

Crear el archivo `.env` basado en `.env.example`:

```ini
# Base de Datos Local (SQLite)
DATABASE_URL=sqlite:///./local.db

# Base de Datos de Producción (PostgreSQL en Vercel, Neon o Supabase)
# DATABASE_URL=postgresql://usuario:contrasena@host:5432/nombre_db

# Cloudflare Turnstile
# En desarrollo (ENVIRONMENT=development) puede dejarse vacío o usar las claves de test de Cloudflare:
#   Site Key: 1x00000000000000000000AA
#   Secret Key: 1x0000000000000000000000000000000AA
TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA

# Entorno
ENVIRONMENT=development

# Configuración JWT para el Panel Administrativo
JWT_SECRET_KEY=tu-clave-secreta-super-larga-y-aleatoria-para-produccion
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
ALLOWED_ORIGINS=*
```

---

## 💻 Puesta en Marcha Local

### 1. Entorno Virtual Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Inicialización de Base de Datos
```bash
cp .env.example .env
python scripts/setup_db.py
```
> La API también crea las tablas automáticamente al iniciar gracias a `init_db()` en `api/index.py`.

### 3. Ejecución

**Opción A: Con Uvicorn (desarrollo directo)**
```bash
uvicorn api.index:app --reload --port 8000
```
- Web principal: [http://localhost:8000](http://localhost:8000)
- Panel de control: [http://localhost:8000/admin.html](http://localhost:8000/admin.html)
- Documentación interactiva Swagger: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

**Opción B: Con Vercel CLI (emulación idéntica a producción)**
```bash
npx vercel dev
```

---

## 🚀 Guía de Instalación y Despliegue en Vercel (Paso a Paso)

El proyecto está preparado de forma nativa para funcionar en **Vercel** como un frontend estático combinado con **Python Serverless Functions** (`/api/*`).

### Requisitos Previos
1. Una cuenta en [Vercel](https://vercel.com).
2. El repositorio subido a tu cuenta de **GitHub**, **GitLab** o **Bitbucket**.
3. Una base de datos PostgreSQL (Vercel Postgres, Neon, Supabase, etc.).

---

### Paso 1: Importar el Proyecto en Vercel
1. Ingresá a tu panel de Vercel y hacé clic en **"Add New..." > "Project"**.
2. Seleccioná el repositorio del proyecto (`gc-seg`).
3. En **Framework Preset**, dejalo en **Other** (el archivo `vercel.json` se encarga del enrutamiento).
4. En **Root Directory**, dejalo en `./`.

---

### Paso 2: Crear y Vincular la Base de Datos PostgreSQL
> ⚠️ **Importante:** SQLite **NO** funciona en Vercel porque el sistema de archivos serverless es de solo lectura y efímero entre ejecuciones. En producción es obligatorio usar PostgreSQL.

**Opción A: Vercel Postgres / Neon integrado (Recomendado)**
1. En la pestaña **Storage** de tu panel de Vercel, hacé clic en **Create Database** y elegí **Postgres** (desarrollado por Neon).
2. Aceptá los términos y dale un nombre (ej: `gc-seg-db`).
3. Una vez creada, hacé clic en **Connect Project** y seleccioná tu proyecto. Vercel inyectará automáticamente las variables `POSTGRES_URL`, `POSTGRES_PRISMA_URL`, etc.

**Opción B: Base de datos externa (Supabase / Neon / Render / AWS RDS)**
- Simplemente agregá la variable de entorno `DATABASE_URL` con el connection string de tu base (ej: `postgresql://usuario:pass@host:5432/nombre_db`).

---

### Paso 3: Configurar Variables de Entorno en Vercel
En la sección **Settings > Environment Variables** de tu proyecto en Vercel, configurá las siguientes variables para el entorno **Production**:

| Variable | Valor / Ejemplo | Descripción |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Activa validaciones estrictas y modo productivo |
| `JWT_SECRET_KEY` | *(cadena aleatoria larga, ej: `openssl rand -hex 32`)* | Clave secreta para firmar los tokens de sesión del panel admin |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Duración del token de sesión (8 horas) |
| `TURNSTILE_SITE_KEY` | *(Tu Site Key de Cloudflare)* | Clave pública del widget de seguridad |
| `TURNSTILE_SECRET_KEY` | *(Tu Secret Key de Cloudflare)* | Clave secreta para validación de bots en el backend |
| `ALLOWED_ORIGINS` | `*` o `https://tu-dominio.com` | Orígenes CORS permitidos |

---

### Paso 4: Obtener las claves de Cloudflare Turnstile (Gratis)
1. Entrá a [dash.cloudflare.com](https://dash.cloudflare.com) (podés crear una cuenta gratuita sin ingresar tarjeta).
2. En el menú lateral, seleccioná **Turnstile** > **Add Site**.
3. **Site name:** `Giaconi-Capra PAS`
4. **Domain:** Agregá tu dominio de Vercel (ej: `tu-proyecto.vercel.app`) y tu dominio definitivo (ej: `giaconi-capra.com.ar`).
5. **Widget Mode:** Elegí **Managed** o **Invisible**.
6. Guardá y copiá la **Site Key** y la **Secret Key** a las variables de entorno de Vercel.

---

### Paso 5: Inicializar las Tablas e Índices
Aunque la API ejecuta `init_db()` automáticamente al arrancar, se recomienda ejecutar el DDL para asegurar todos los índices:
1. Abrí la pestaña **Storage** en Vercel > tu base de datos Postgres > consola **Query / SQL Editor**.
2. Copiá y pegá el contenido completo de [`scripts/init_db.sql`](scripts/init_db.sql) y ejecutalo.
3. *(Opcional)* Si deseás precargar los testimonios de prueba, copiá y ejecutá también [`scripts/seed_data.sql`](scripts/seed_data.sql).

---

### Paso 6: Desplegar y Configurar el Administrador Inicial
1. Hacé clic en **Deploy** en Vercel.
2. Una vez finalizado el build, ingresá a la URL de tu aplicación:
   - Sitio público: `https://tu-proyecto.vercel.app/`
   - Panel de control: `https://tu-proyecto.vercel.app/admin.html`
3. Al entrar a `admin.html` por primera vez, el sistema detectará que no existen administradores y te mostrará la pantalla de **Setup Inicial** para crear el usuario **Superadministrador Principal**.
4. ¡Listo! Ya podés administrar cotizaciones, coberturas, manuales PDF, testimonios y preguntas frecuentes en vivo.

---

## 🛡️ Panel de Administración (`admin.html`)

El panel es una **SPA (Single-Page Application)** accesible en `/admin.html`:

1. **Bootstrap inicial:** Si la tabla `admin_users` está vacía, el sistema muestra automáticamente la pantalla de configuración del primer superadministrador.
2. **Pestañas disponibles:**
   - 📋 **Cotizaciones:** Listado de leads, buscador en tiempo real, filtro por estado (`nuevo`, `contactado`, `en_gestion`, `cerrado`), modal de detalle con IP y botón directo para abrir conversación en WhatsApp.
   - ⭐ **Testimonios:** Aprobación/ocultamiento con un click, creación manual y edición.
   - 👥 **Administradores:** Creación de usuarios con roles `admin` y `superadmin`, cambio de contraseña y eliminación protegida.
   - 📚 **Manuales:** Carga de documentos PDF (hasta 4 MB) vinculados dinámicamente a las coberturas existentes.
   - 🛡️ **Coberturas:** Creación y edición completa de pólizas de Personas y Empresas (título, descripción, icono de Lucide, badge, orden y toggle activo/inactivo).
   - ❓ **FAQs:** Gestión de preguntas frecuentes para la web.

---

## 📡 Catálogo de Endpoints de la API

| Método | Endpoint | Autenticación | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Pública | Estado general de la API y conexión a base de datos |
| `GET` | `/api/config` | Pública | Configuración pública (Turnstile site key) |
| `POST` | `/api/contact` | Turnstile + Rate Limit (10/min) | Enviar formulario de cotización |
| `GET` | `/api/reviews` | Pública | Listar testimonios aprobados para la web |
| `POST` | `/api/reviews` | Turnstile + Rate Limit (10/min) | Publicar nueva opinión de cliente |
| `GET` | `/api/coverages` | Pública | Listar coberturas activas (filtro `?categoria=`) |
| `GET` | `/api/faqs` | Pública | Listar preguntas frecuentes activas |
| `GET` | `/api/manuals` | Pública | Listar metadatos de manuales PDF |
| `GET` | `/api/manuals/{id}/download` | Pública | Descarga o visualización del PDF |
| `GET` | `/api/auth/setup-status` | Pública | Informa si el sistema requiere primer administrador |
| `POST` | `/api/auth/setup` | Pública (solo si vacía) | Crear primer superadministrador |
| `POST` | `/api/auth/login` | Pública | Iniciar sesión (retorna Bearer Token) |
| `GET` | `/api/auth/me` | JWT | Perfil del administrador autenticado |
| `GET` | `/api/admin/stats` | JWT | Métricas globales del dashboard |
| `GET/POST` | `/api/admin/leads` | JWT | Listar y crear cotizaciones |
| `PATCH/DELETE` | `/api/admin/leads/{id}` | JWT | Actualizar estado o eliminar cotización |
| `GET/POST` | `/api/admin/reviews` | JWT | Listar y crear testimonios |
| `PUT/DELETE` | `/api/admin/reviews/{id}` | JWT | Editar, aprobar/ocultar o eliminar testimonio |
| `GET/POST` | `/api/coverages/admin` | JWT | Listar y dar de alta coberturas |
| `PUT/DELETE` | `/api/coverages/admin/{id}` | JWT | Modificar o eliminar cobertura |
| `GET/POST` | `/api/faqs/admin` | JWT | Listar y dar de alta preguntas frecuentes |
| `PUT/DELETE` | `/api/faqs/admin/{id}` | JWT | Modificar o eliminar pregunta frecuente |
| `GET/POST` | `/api/admin/manuals` | JWT | Listar y subir manuales PDF |
| `DELETE` | `/api/admin/manuals/{id}` | JWT | Eliminar manual |
| `GET/POST` | `/api/admin/users` | JWT | Listar y dar de alta administradores |
| `PUT` | `/api/admin/users/{id}/password`| JWT | Modificar contraseña de un administrador |
| `DELETE` | `/api/admin/users/{id}` | JWT | Eliminar administrador con validación de seguridad |
