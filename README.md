# Giaconi-Capra® PAS — Website & Insurance Quote Manager

Corporate website and insurance quote platform for **Giaconi-Capra® Productores Asesores de Seguros**. Built as a static frontend (Tailwind CSS + Alpine.js) backed by a **serverless FastAPI (Python) API**, flexible persistence (**SQLite locally / PostgreSQL in production**) and an integrated **Admin Panel (CRUD)**.

---

## 🚦 Project Status (Read First)

This repository currently contains **two landing pages**:

| File | Role | Description |
| :--- | :--- | :--- |
| `index.html` | **POC** (Proof of Concept) | The page currently served at `/`. Uses **in-memory mock data only**: the contact form shows a success message without calling the API, and testimonials are a hardcoded array. Nothing is persisted. |
| `index-new.html` | **MVP** (in development) | The real product under active development. Wired to the backend API (`/api/contact`, `/api/reviews`). ✅ Data persistence fixed (see [Known Issues](#-known-issues)). |
| `admin.html` | Admin Panel | Fully functional SPA (JWT auth + CRUD). Works against the backend API. |

The MVP (`index-new.html`) will replace the POC in production once development is complete.

---

## 🚀 Features

* **Responsive UI:** Built with Tailwind CSS, adapted to mobile, tablet and desktop.
* **Interactive Coverage Catalog:** Tabs (Individuals / Business) and modals with product details.
* **Contact & Quote Form:** Real-time validation (email format, phone sanitization, character limits, Ley 25.326 consent).
* **Cloudflare Turnstile:** Server-side anti-bot verification on the quote form and public reviews modal (safe bypass for development/localhost).
* **Dynamic Testimonials Carousel:** Reads published reviews from the backend; visitors can submit their own (*MVP only*).
* **Admin Panel (`admin.html`):** Dashboard for CRUD management of quote requests (`contact_leads`) and review moderation (`reviews`), with direct WhatsApp links.
* **Dual Persistence (SQLite / PostgreSQL):** Transparent connection via SQLAlchemy.
* **Serverless Architecture for Vercel:** Decoupled frontend with Python Serverless Functions and an optimized connection pool.
* **WhatsApp Integration:** Floating button and priority chat contact option.

---

## 🛠️ Tech Stack

### Frontend
* **HTML5 Semantic Structure**
* **Tailwind CSS v3** (CDN / custom brand config)
* **Alpine.js v3** + `@alpinejs/collapse`
* **Lucide Icons**
* **Google Fonts** (Plus Jakarta Sans)
* **Cloudflare Turnstile**

### Backend & Persistence
* **Python 3.12+ / FastAPI** (REST endpoints + automatic OpenAPI docs)
* **SQLAlchemy 2.0 & Pydantic v2** (ORM, schema validation/sanitization)
* **PostgreSQL / SQLite** (Vercel Postgres, Neon, Supabase, or local SQLite)
* **HTTPX** (async client for the Cloudflare Turnstile API)
* **PyJWT + bcrypt** (admin authentication)

---

## 📂 Project Structure

```text
.
├── .vscode/
│   └── launch.json             # F5 debugging config for VS Code
├── api/                        # Serverless FastAPI backend
│   ├── index.py                # ASGI entrypoint
│   ├── config.py               # Settings & env loading (.env.local / .env)
│   ├── database.py             # SQLAlchemy engine & connection pool
│   ├── models.py               # Relational database models
│   ├── schemas.py              # Pydantic validation schemas
│   ├── auth.py                 # Security helpers (bcrypt hashing, JWT tokens, middleware)
│   ├── routes/
│   │   ├── auth.py             # Login, initial setup (/api/auth/*)
│   │   ├── contact.py          # POST /api/contact (quote submissions)
│   │   ├── reviews.py          # GET & POST /api/reviews (public reviews)
│   │   ├── admin.py            # CRUD endpoints for the dashboard (/api/admin/*)
│   │   └── health.py           # GET /api/health (health check)
│   └── services/
│       └── turnstile.py        # Cloudflare Turnstile verification service
├── scripts/                    # Database scripts & utilities
│   ├── init_db.sql             # DDL for tables and indexes
│   ├── seed_data.sql           # Initial testimonials
│   └── setup_db.py             # Python auto-initialization script
├── img/                        # Graphics & insurance company logos
├── index.html                  # POC landing (mock/in-memory data) — currently live at /
├── index-new.html              # MVP landing (API-connected) — in development
├── admin.html                  # Admin panel SPA (JWT auth + CRUD)
├── requirements.txt            # Python dependencies for Vercel
├── vercel.json                 # Vercel routing/rewrites config
├── .env.example                # Environment variables template
├── local.db                    # Local SQLite database (not committed)
└── README.md                   # This file
```

---

## 🗄️ Database Schema

### 1. `contact_leads` (Quote Requests)
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unique identifier |
| `nombre` | `VARCHAR(100)` | Full name |
| `telefono` | `VARCHAR(50)` | Phone / WhatsApp |
| `email` | `VARCHAR(255)` | Email address |
| `producto` | `VARCHAR(100)` | Coverage of interest |
| `mensaje` | `TEXT` | Message or details |
| `wsp_preferred` | `BOOLEAN` | Prefers WhatsApp contact |
| `aceptar_datos` | `BOOLEAN` | Ley 25.326 consent |
| `ip_address` | `VARCHAR(45)` | Client IP |
| `user_agent` | `TEXT` | Browser/device |
| `status` | `VARCHAR(20)` | Status (`nuevo`, `contactado`, `en_gestion`, `cerrado`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Creation timestamp |

### 2. `reviews` (Client Testimonials)
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unique identifier |
| `name` | `VARCHAR(100)` | Author name |
| `role` | `VARCHAR(100)` | Role or coverage |
| `avatar` | `VARCHAR(10)` | Avatar initials (e.g., `CM`) |
| `rating` | `SMALLINT` | 1 to 5 stars |
| `text` | `TEXT` | Review text |
| `is_approved` | `BOOLEAN` | Moderation / web visibility flag |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Publication date |

### 3. `admin_users` (Admin Users)
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unique identifier |
| `username` | `VARCHAR(50) UNIQUE` | Unique username |
| `email` | `VARCHAR(255) UNIQUE` | Unique email |
| `hashed_password` | `VARCHAR(255)` | bcrypt hash (12 rounds) |
| `full_name` | `VARCHAR(100)` | Full name |
| `role` | `VARCHAR(20)` | Role (`superadmin`, `admin`) — *note: roles are stored but not yet enforced* |
| `is_active` | `BOOLEAN` | Account status |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Registration date |
| `last_login` | `TIMESTAMP WITH TIME ZONE` | Last login date |

---

## ⚙️ Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Available variables:

```ini
# Option 1: Local SQLite database (fast local development, no server needed)
DATABASE_URL=sqlite:///./local.db

# Option 2: PostgreSQL (Vercel Postgres, Neon, Supabase or local)
# DATABASE_URL=postgresql://user:password@localhost:5432/gc_seg_db

# Cloudflare Turnstile (anti-bot)
# Leave empty in development for an automatic bypass (ENVIRONMENT=development),
# or use Cloudflare's official test keys (always pass):
#   TURNSTILE_SITE_KEY=1x00000000000000000000AA
#   TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
# For production, get your keys at: https://dash.cloudflare.com/ -> Turnstile
TURNSTILE_SECRET_KEY=
TURNSTILE_SITE_KEY=

# Environment: development | production
ENVIRONMENT=development

# JWT settings for the admin panel (REQUIRED in production)
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# Allowed CORS origins (optional, defaults to all)
ALLOWED_ORIGINS=*
```

Notes:
* **Turnstile bypass (dev only):** with `ENVIRONMENT=development` and no `TURNSTILE_SECRET_KEY` configured, verification is skipped so you can test without Cloudflare credentials. **Warning:** in `production` a missing secret makes every form submission fail.
* **JWT secret:** the code ships with an insecure fallback value for development. **Always** set `JWT_SECRET_KEY` to a long random string in production — anyone who knows the fallback can forge admin tokens.
* **SQLite path anchoring:** relative SQLite URLs (e.g. `sqlite:///./local.db`) are always resolved against the **project root**, regardless of the process working directory. This matters because `vercel dev` runs the Python function from `.vercel/cache/index_py/` — without anchoring, writes used to land in a throwaway database inside that cache.

---

## 💻 Local Development (Conda on WSL / Linux)

### 1. Create and activate the Conda environment
```bash
conda create -n gc-seg python=3.12 -y
conda activate gc-seg
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env` and initialize the database
```bash
cp .env.example .env
python scripts/setup_db.py   # optional: tables are also auto-created on API startup
```

> The API automatically creates the database tables on startup if they don't exist (idempotent). `setup_db.py` is still useful to seed the initial testimonials.

### 4. Run the project

#### Recommended: full Vercel simulation
```bash
npx vercel dev
```
This emulates the Vercel router, serving frontend and backend under a single port:
* Landing (POC): [http://localhost:3000](http://localhost:3000)
* MVP preview: [http://localhost:3000/index-new.html](http://localhost:3000/index-new.html)
* Admin Panel: [http://localhost:3000/admin.html](http://localhost:3000/admin.html)

> ⚠️ **The frontend calls relative API paths (`/api/*`).** A plain static file server (e.g. `python -m http.server`) will **not** proxy those calls to FastAPI — forms and testimonials will fail in that setup. If you want to run the backend standalone for API work, use uvicorn (`uvicorn api.index:app --reload --port 8000`) alongside `npx vercel dev` is unnecessary; use it only with Swagger UI for direct endpoint testing at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

---

## 🛡️ Admin Panel (`admin.html`)

The panel is a **SPA (Single-Page Application)** with full JWT authentication, available at `/admin.html`:

### Authentication System

**First run (bootstrap):** if the `admin_users` table is empty, the panel automatically shows an initial setup form to create the first administrator with the `superadmin` role.

**Afterwards:** a secure login form (username/email + password). The JWT is stored in `localStorage` and validated automatically on page reload.

**Security implemented:**
- 🔐 Passwords hashed with **bcrypt** (12 salt rounds)
- 🎟️ Signed **JWT** tokens (HS256), configurable expiration (default: 8 hours)
- 🚫 All `/api/admin/*` endpoints require a valid Bearer Token (HTTP 401 otherwise)
- 🛡️ Safeguards: you cannot delete your own account nor the last remaining admin

### Dashboard Features

1. **Real-time metrics:** total requests, pending, reviews, admins and average rating.
2. **Request manager (`contact_leads`):** live search, status filter, one-click status changes, direct **WhatsApp** button, full detail modal (IP, agent, date) and deletion with confirmation.
3. **Review manager (`reviews`):** manual creation, editing (name, role, stars, text), visibility toggle (publish/hide) and deletion with confirmation.
4. **Admin user manager (`admin_users`):** list users, create new admins, change passwords, delete users with safeguards.

---

## 🐞 Debugging in Visual Studio Code

The repo includes a ready-to-use `.vscode/launch.json` for debugging the backend with breakpoints:

1. **Select the interpreter:** `Ctrl + Shift + P` → `Python: Select Interpreter` → choose `gc-seg` (Conda).
2. **Set breakpoints** in any file under `api/` (e.g. `api/routes/contact.py`).
3. **Start debugging:** press `F5` (**Python: FastAPI (Backend gc-seg)**).
4. The debugger will pause at your breakpoints when requests arrive from the frontend or Swagger.

---

## 🚀 Deployment on Vercel

1. **Import the repository** into Vercel from GitHub.
2. **Create or link a PostgreSQL database:**
   - In the project's **Storage** tab, create a **Vercel Postgres** database (or link **Neon** / **Supabase**).
   - Vercel will automatically inject `POSTGRES_URL` (used by `api/config.py`).

   > ⚠️ **SQLite does NOT work on Vercel.** Serverless filesystems are read-only (except `/tmp`) and ephemeral across invocations — writes fail or disappear. **PostgreSQL is mandatory in production.**
3. **Run the DDL scripts** in the Vercel Storage SQL console (or your SQL client):
   - `scripts/init_db.sql`
   - `scripts/seed_data.sql` (optional — initial reviews)
4. **Set environment variables** in the Vercel dashboard:
   - `TURNSTILE_SECRET_KEY` / `TURNSTILE_SITE_KEY`: your real Cloudflare Turnstile keys.
   - `JWT_SECRET_KEY`: a long, random secret for signing admin JWTs.
   - `ENVIRONMENT`: `production`
5. **Deploy.** Vercel builds the Serverless Function in `/api/*` and serves static files from the root.
   - Note: `index.html` (the POC) is served at `/`. To make the MVP live, promote `index-new.html` to `index.html`.
6. **First admin access:** open `https://your-domain.vercel.app/admin.html`. If `admin_users` is empty, the system will guide you through creating the first administrator.

---

## 🐛 Known Issues

1. **The live landing (`/`) is the POC:** form submissions and reviews are in-memory mocks; nothing is stored. Expected behavior until the MVP (`index-new.html`) is promoted to `index.html`.
2. **No rate limiting** on `/api/auth/login` or the public forms.
3. **Admin roles are partially enforced:** deleting a `superadmin` requires being a `superadmin` and the system always keeps at least one. Role checks are not applied to other actions (creating admins, changing passwords) yet.

### Recently Fixed

* ✅ **MVP data persistence** (`index-new.html`): relative SQLite URLs are now anchored to the project root — `vercel dev` runs functions from `.vercel/cache/index_py/`, and writes previously landed in a throwaway database inside that cache. Tables are also auto-created on startup, and the API logs a loud error if SQLite is used on Vercel (where only PostgreSQL persists).
* ✅ **Anti-bot widget key mismatch:** the MVP fetches the site key from `GET /api/config`, so frontend and backend never use mismatched key pairs (mismatches made every submission fail with HTTP 400).
* ✅ **Validation gaps closed:** review `rating` is bounded to 1–5 (Pydantic + DB `CHECK` constraint, mirrored in `init_db.sql`), lead `status` only accepts `nuevo|contactado|en_gestion|cerrado`, and admin `role` only accepts `admin|superadmin`.

---

## 📡 API Overview

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | — | Health check + DB connectivity |
| `GET` | `/api/config` | — | Public config (Turnstile site key, environment) |
| `POST` | `/api/contact` | Turnstile | Submit a quote request |
| `GET` | `/api/reviews` | — | List approved reviews |
| `POST` | `/api/reviews` | Turnstile | Submit a public review |
| `GET` | `/api/auth/setup-status` | — | Whether the panel needs initial setup |
| `POST` | `/api/auth/setup` | — | Create the first admin (only when none exist) |
| `POST` | `/api/auth/login` | — | Login, returns JWT |
| `GET` | `/api/auth/me` | JWT | Current admin profile |
| `GET` | `/api/admin/stats` | JWT | Dashboard metrics |
| `GET/POST` | `/api/admin/leads` | JWT | List / create leads |
| `PATCH/DELETE` | `/api/admin/leads/{id}` | JWT | Update status / delete lead |
| `GET/POST` | `/api/admin/reviews` | JWT | List / create reviews |
| `PUT/DELETE` | `/api/admin/reviews/{id}` | JWT | Edit / moderate / delete review |
| `GET/POST` | `/api/admin/users` | JWT | List / create admin users |
| `PUT` | `/api/admin/users/{id}/password` | JWT | Change an admin's password |
| `DELETE` | `/api/admin/users/{id}` | JWT | Delete an admin (with safeguards) |

Interactive docs (Swagger UI): `/api/docs` — OpenAPI spec: `/api/openapi.json`.

> Note: routes are intentionally registered both with and without the `/api` prefix (Vercel rewrite compatibility), so Swagger shows duplicated entries.
