# ADTU Notes — Backend API

FastAPI + MongoDB + Cloudinary backend for a college Notes Sharing Platform. It serves your existing React
frontend (React Router, Tailwind, React Icons) and does **not** include any frontend code.

* **Public (no login):** browse faculties/departments, search notes, open/download PDF & DOCX, view uploader profiles.
* **Logged-in users:** save notes, request departments, edit their profile.
* **Uploaders:** upload / edit / replace / delete their own notes, see their upload statistics.
* **Admins:** manage faculties, departments, requests, users and roles, moderate notes, view the dashboard and audit trail.

Stack: Python 3.11+, FastAPI, async PyMongo, Pydantic v2, Cloudinary, JWT in HttpOnly cookies, Argon2, Pytest + HTTPX.

---

## Table of contents
1. [Prerequisites](#1-prerequisites)
2. [Python virtual environment](#2-python-virtual-environment)
3. [Install dependencies](#3-install-dependencies)
4. [MongoDB (local or Atlas)](#4-mongodb-local-or-atlas)
5. [Cloudinary](#5-cloudinary)
6. [Configure `.env`](#6-configure-env)
7. [Start the server](#7-start-the-server)
8. [Create the first admin](#8-create-the-first-admin)
9. [Seed sample faculties & departments](#9-seed-sample-faculties--departments)
10. [Run the tests](#10-run-the-tests)
11. [Connect your React frontend](#11-connect-your-react-frontend)
12. [Try the API in `/docs`](#12-try-the-api-in-docs)
13. [Production deployment](#13-production-deployment)
14. [API reference](#14-api-reference)
15. [Security design](#15-security-design)
16. [Behaviour you should know about](#16-behaviour-you-should-know-about)
17. [Troubleshooting](#17-troubleshooting)

Project layout:

```
backend/
├── app/
│   ├── main.py                  app factory, CORS, CSRF middleware, startup (indexes)
│   ├── core/                    config, security (Argon2/JWT), permissions, exceptions, cookies, csrf, rate_limit
│   ├── db/                      mongodb.py (connection), indexes.py (all indexes, created on startup)
│   ├── models/                  document builders + enums for each collection
│   ├── schemas/                 Pydantic request/response models (camelCase JSON)
│   ├── api/                     dependencies.py (auth/role guards) and routes/*.py
│   ├── services/                business logic: auth, notes, departments, admin, saved notes, cloudinary, audit
│   └── utils/                   file_validation.py, serialization.py, text.py
├── scripts/                     create_admin.py, seed_data.py
├── tests/                       68 tests (real MongoDB test DB, Cloudinary mocked)
├── docs/react-integration.md    Axios client, auth context, every endpoint's JSON
├── .env.example  docker-compose.yml  pytest.ini  requirements.txt
```

---

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.11 or newer | `python --version` |
| MongoDB | 4.4+ (local, Docker, or Atlas free tier) | see §4 |
| A Cloudinary account | free plan is fine | see §5 |
| Git (optional) | any | |

On Windows use **PowerShell**. On macOS/Linux use a normal terminal. All commands are run inside the `backend/` folder.

## 2. Python virtual environment

```bash
cd backend

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
#   (if PowerShell blocks it: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)

# Windows cmd.exe
python -m venv .venv
.venv\Scripts\activate.bat
```
Your prompt should now start with `(.venv)`.

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. MongoDB (local or Atlas)

Pick **one** option. The app creates every collection and index automatically on startup.

**Option A — Docker (easiest locally)**
```bash
docker compose up -d          # starts MongoDB 7 on 127.0.0.1:27017
```
Then `MONGODB_URL=mongodb://localhost:27017`.

**Option B — Installed MongoDB Community Server**
Install from <https://www.mongodb.com/try/download/community>, make sure the service is running, and use
`MONGODB_URL=mongodb://localhost:27017`.

**Option C — MongoDB Atlas (cloud, free tier)**
1. Create a free cluster at <https://www.mongodb.com/atlas>.
2. *Database Access* → add a database user (username + password).
3. *Network Access* → add your current IP (for production add your server's IP; avoid `0.0.0.0/0`).
4. *Connect* → *Drivers* → copy the connection string:
   `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority`
5. Put it in `.env` as `MONGODB_URL`. If the password contains special characters (`@ : / ? #`),
   URL-encode them (`@` → `%40`).

The data lives in the database named by `MONGODB_DB_NAME` (default `adtu_notes`).

## 5. Cloudinary

1. Sign up at <https://cloudinary.com> (free).
2. Dashboard → **API Keys** (or *Programmable Media → Dashboard*): copy **Cloud name**, **API Key**, **API Secret**.
3. **Important for PDFs:** Settings → **Security** → enable **“Allow delivery of PDF and ZIP files”**.
   New free accounts block PDF delivery by default, and PDF links would return `401` until this is ticked.
4. Put the three values in `.env` (§6). The secret stays on the server; it is never sent to React.

Files are stored as Cloudinary `raw` assets in the folder `CLOUDINARY_FOLDER` (default `adtu-notes/notes`).
MongoDB stores only the URL, public ID, type and size.

## 6. Configure `.env`

```bash
# macOS / Linux
cp .env.example .env
# Windows
copy .env.example .env
```
Generate a strong JWT secret and paste it into `JWT_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

| Variable | Required | Meaning |
|---|---|---|
| `MONGODB_URL` | yes | MongoDB connection string |
| `MONGODB_DB_NAME` | no (`adtu_notes`) | database name |
| `JWT_SECRET_KEY` | yes (≥32 chars) | signs tokens. Never commit it |
| `FRONTEND_ORIGINS` | yes | comma-separated exact origins allowed by CORS, e.g. `http://localhost:5173`. No `*` |
| `ENVIRONMENT` | no | `development` / `testing` / `production` (production forces secure cookies) |
| `ENABLE_DOCS` | no (`true`) | serve `/docs`. Set `false` in production if you prefer |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | no (15 / 7) | session lifetimes |
| `COOKIE_SECURE` | no | blank = automatic (true in production). Must be true with `SAMESITE=none` |
| `COOKIE_SAMESITE` | no (`lax`) | `lax`, `strict` or `none` |
| `COOKIE_DOMAIN` | no | e.g. `.example.com` to share cookies between `app.` and `api.` subdomains |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | for uploads | from §5 |
| `CLOUDINARY_FOLDER` | no | upload folder |
| `MAX_UPLOAD_SIZE_MB` | no (10) | per-file limit |
| `MAX_SEMESTERS` | no (8) | highest allowed semester number |
| `RATE_LIMIT_ENABLED` | no (`true`) | login/register/refresh/upload/request throttling |
| `TRUST_PROXY_HEADERS` | no (`false`) | set `true` only behind your own reverse proxy (reads `X-Forwarded-For`) |
| `ADMIN_NAME/USERNAME/EMAIL/PASSWORD` | only for §8 | credentials for the first admin |

The app refuses to start if `JWT_SECRET_KEY` is too short or `FRONTEND_ORIGINS` contains `*`.

## 7. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```
* API base: `http://localhost:8000/api`
* Interactive docs: `http://localhost:8000/docs`
* Health check: `http://localhost:8000/api/health` → `{"status":"ok"}`

(`--reload` is for development only.)

## 8. Create the first admin

Nobody can become admin through registration or profile updates. Create the first admin from the command line.

1. In `.env` set `ADMIN_NAME`, `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
   (password: 8+ chars with upper, lower and a digit).
2. Run:
```bash
python -m scripts.create_admin
```
* Safe to re-run: if **any** administrator already exists, it does nothing, so no duplicate admins.
* If that email already belongs to a normal user: `python -m scripts.create_admin --promote`.
* Afterwards remove `ADMIN_PASSWORD` from `.env`. Further admins/uploaders are made from the admin API
  (`PATCH /api/admin/users/{id}/role`).

## 9. Seed sample faculties & departments

```bash
python -m scripts.seed_data
```
Creates sample faculties and departments (edit `SAMPLE` in `scripts/seed_data.py` first to match your college).
Idempotent; existing records are kept.

## 10. Run the tests

MongoDB must be running (§4). Tests use a **separate throw-away database** that is dropped at the end, and
Cloudinary is replaced by an in-memory fake, so no Cloudinary credentials are needed and your real data is never touched.
```bash
pytest -q                                   # ~1 minute (Argon2 hashing is deliberately slow)
pytest tests/test_notes.py -q               # one file
TEST_MONGODB_URL="mongodb://localhost:27017" pytest -q     # use another MongoDB for tests
```
The suite covers: registration/duplicates, password hashing, login/refresh/logout, CSRF, rate limiting,
public browsing without login, anonymous/non-uploader upload rejection, ownership on edit/replace/delete,
file validation failures, Cloudinary compensation on DB failure, saved notes (access control, no duplicates),
department requests and admin approve/reject, admin authorization, role changes and last-admin protection,
invalid ObjectIds, pagination, filters and query-injection safety.

## 11. Connect your React frontend

1. Backend `.env`: `FRONTEND_ORIGINS=http://localhost:5173` (your Vite/CRA dev URL, exact, no trailing slash).
2. Frontend `.env`: `VITE_API_URL=http://localhost:8000/api`.
3. Create the Axios client with **`withCredentials: true`** and the CSRF header, plus the `AuthContext`
   from **[docs/react-integration.md](docs/react-integration.md)** — it also lists every request/response shape
   (login, paginated search, multipart upload, saved notes, admin) for each of your pages.
4. After login, the user and role come from `GET /api/auth/me` (`user.role` is `user`, `uploader` or `admin`).

How auth works for the browser: login sets two **HttpOnly** cookies (access token 15 min, refresh token 7 days) plus a
readable `csrf_token` cookie. JavaScript cannot read the tokens. For `POST/PUT/PATCH/DELETE` the frontend sends the
CSRF value in the `X-CSRF-Token` header (returned by `/auth/login`, `/auth/refresh`, `/auth/csrf`).

## 12. Try the API in `/docs`

1. Open `http://localhost:8000/docs`.
2. **Public endpoints** (faculties, departments, notes) work immediately with *Try it out*.
3. **Log in:** `POST /api/auth/login` with your admin e-mail/password. The browser stores the cookies automatically.
   Copy the `csrfToken` from the response.
4. Click **Authorize** (top right), paste the token in the **CSRF** box, **Authorize**.
   Now write requests (POST/PATCH/DELETE) work too. GET requests only need the cookie.
5. To test uploads use `POST /api/notes` → choose a `.pdf` or `.docx`. The user must have the `uploader` role:
   as admin, `PATCH /api/admin/users/{id}/role` with `{"role": "uploader"}` for a registered user, then log in as that user.

## 13. Production deployment

* **HTTPS only.** Set `ENVIRONMENT=production` (forces `Secure` cookies; the app refuses to start otherwise).
* **Same site for cookies.** Best: serve the React app and the API under one parent domain
  (`app.example.com` + `api.example.com`) with `COOKIE_DOMAIN=.example.com`, `COOKIE_SAMESITE=lax`.
  Fully separate domains need `COOKIE_SAMESITE=none` (+ HTTPS), but browsers increasingly block such third-party cookies.
* `FRONTEND_ORIGINS=https://app.example.com` (exact).
* Run without `--reload`, e.g. `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
  behind a reverse proxy (Nginx/Caddy/your host’s router). Then set `TRUST_PROXY_HEADERS=true` so rate limiting sees real client IPs.
* **Rate limiting is in-memory per process.** With several workers/instances each has its own counters; put a shared
  limiter (e.g. Redis, or limits at the proxy/WAF) in front for strict protection.
* `ENABLE_DOCS=false` if you do not want public API docs.
* Use MongoDB Atlas (or a replica set) with backups, a least-privilege DB user and an IP allow-list.
* Store secrets in your host’s secret manager, never in git. Rotate `JWT_SECRET_KEY` to log everybody out.
* Cloudinary: keep the API secret server-side only; remember the PDF-delivery setting (§5).
* Monitor the logs for `ORPHANED Cloudinary asset` (see §16) and `Unhandled …` errors. Logs never contain passwords, tokens or secrets.
* Use `GET /api/health` for the platform health check.
* Not included (not in your spec): e-mail verification, password reset by e-mail, virus scanning of uploads.

## 14. API reference

Base path `/api`. **Auth** column: 🌐 public · 🔑 any logged-in user · ⬆️ uploader · 🛡️ admin.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | 🌐 | create account (role always `user`) |
| POST | `/auth/login` | 🌐 | sign in, sets cookies, returns user + `csrfToken` |
| POST | `/auth/logout` | 🌐 | revoke session, clear cookies |
| POST | `/auth/refresh` | cookie | rotate refresh token, new access token |
| GET | `/auth/csrf` | 🌐 | get/restore the CSRF token |
| GET / PATCH | `/auth/me` | 🔑 | current user / update name, username, password |
| GET | `/faculties`, `/faculties/{id}` | 🌐 | faculties |
| GET | `/departments`, `/departments/{id}` | 🌐 | departments (`?facultyId=`) |
| POST | `/departments/requests` | 🔑 | request a new department |
| GET | `/departments/requests/mine` | 🔑 | my requests |
| GET | `/notes` | 🌐 | search/list (`q, facultyId, departmentId, semester, username, fileType, page, limit, sortBy, sortOrder`) |
| GET | `/notes/{id}` | 🌐 | note details (unpublished: owner/admin only) |
| POST | `/notes` | ⬆️ | upload (multipart) |
| GET | `/notes/mine` | ⬆️ | my notes + statistics |
| PATCH | `/notes/{id}` | owner ⬆️ / 🛡️ | edit metadata / moderate (publish/unpublish) |
| PUT | `/notes/{id}/file` | owner ⬆️ | replace file |
| DELETE | `/notes/{id}` | owner / 🛡️ | delete |
| GET | `/users/{username}/public` | 🌐 | public profile + notes |
| GET | `/users/{username}/notes` | 🌐 | public notes of a user |
| GET | `/saved-notes` | 🔑 | my saved notes |
| POST / DELETE | `/saved-notes/{id}` | 🔑 | save / unsave (idempotent) |
| GET | `/admin/department-requests`, `/{id}` | 🛡️ | review queue (`?status=`) |
| PATCH | `/admin/department-requests/{id}/approve` · `/reject` | 🛡️ | decide request |
| POST / PATCH / DELETE | `/admin/faculties[/{id}]` | 🛡️ | manage faculties |
| POST / PATCH / DELETE | `/admin/departments[/{id}]` | 🛡️ | manage departments |
| GET | `/admin/users`, `/admin/users/{id}` | 🛡️ | users (`?q=&role=&isActive=`) |
| PATCH | `/admin/users/{id}/role` · `/status` | 🛡️ | change role / activate-deactivate |
| GET | `/admin/dashboard` | 🛡️ | counts + recent activity |
| GET | `/health` | 🌐 | health check |

Errors always look like `{"error": {"code": "...", "message": "...", "details": [{"field","message"}]}}`.
Pagination always returns `{items, page, limit, total, totalPages}` (max `limit` 50).

## 15. Security design

* **Passwords:** Argon2id, with a password policy (8–128 chars, upper + lower + digit). Hashes never leave the server.
* **Sessions:** 15-minute access JWT + single-use 7-day refresh token (stored only as a SHA-256 hash). Re-using an
  old refresh token revokes the whole session family. Tokens are in HttpOnly cookies, never in URLs, bodies or logs.
* **CSRF:** double-submit token + Origin allow-list on all cookie-authenticated write requests.
* **Authorization on the server for every protected route;** ownership comes from the authenticated user, never from
  client fields (`uploadedBy`, `role`, … are rejected or ignored). Roles are re-read from the database on each request,
  so role changes and deactivation take effect immediately.
* **Mass-assignment protection:** request models forbid unknown fields on every write except registration (which ignores them).
* **Mongo safety:** typed parameters, ObjectId validation, escaped regex search, allow-listed sort fields, capped page size. No raw client values become query operators.
* **Uploads:** extension + MIME + magic-byte check, DOCX structure/zip-bomb check, size cap (never buffers more than the limit), sanitized names, server-generated storage paths.
* **Privacy:** public responses never contain email, password hash, saved lists or Cloudinary public IDs.
* **Audit trail** for approvals/rejections, faculty/department changes and deletes, role/status changes, note moderation and admin deletions.
* CORS limited to `FRONTEND_ORIGINS`; errors never expose stack traces; unique DB indexes back every uniqueness rule.

## 16. Behaviour you should know about

* **Admins moderate; they don’t upload.** Only the `uploader` role can upload (change `can_upload_notes` in `app/core/permissions.py` to allow admins).
* **Admin moderation of notes** = publish/unpublish or delete. An admin-hidden note cannot be republished by its owner.
* **Deleting faculties/departments is a soft delete** (`isActive=false`) and is refused with `409` while active departments or notes depend on them. Reactivate with `PATCH … {"isActive": true}`.
* **MongoDB and Cloudinary are not atomic together.** Upload: if saving to MongoDB fails, the new Cloudinary file is deleted.
  Replace: the old file is deleted only after the database update succeeds. Delete: the database record goes first, then the file.
  If a Cloudinary delete itself fails, the app logs `ORPHANED Cloudinary asset needs manual cleanup: <publicId>` — it never loses a note because of it.
* Refreshing the session from two tabs at the same instant can trigger the “refresh token reuse” protection and sign you out. That is intentional.
* The last active administrator can’t be demoted or deactivated, and admins can’t deactivate themselves.

## 17. Troubleshooting

| Symptom | Fix |
|---|---|
| `ValidationError … mongodb_url / jwt_secret_key Field required` on start | `.env` missing or not in `backend/`. Run commands from `backend/` |
| `ServerSelectionTimeoutError` | MongoDB isn’t running / wrong `MONGODB_URL` / Atlas IP not allow-listed |
| Browser: CORS error | add the exact frontend origin to `FRONTEND_ORIGINS` and restart; use `withCredentials: true` |
| `403 csrf_failed` | send `X-CSRF-Token` on POST/PUT/PATCH/DELETE (value from login); in `/docs` use **Authorize** |
| `401` right after login from React | cookies blocked: check `withCredentials`, same-site setup (§13), and HTTP vs HTTPS (`COOKIE_SECURE`) |
| `502 storage_not_configured` / `upload_failed` | fill the three `CLOUDINARY_*` values; check the credentials |
| PDF link opens a `401` page | enable “Allow delivery of PDF and ZIP files” in Cloudinary (§5) |
| `413 file_too_large` | raise `MAX_UPLOAD_SIZE_MB` (and your reverse proxy’s body limit) |
| `429 rate_limited` | wait for `Retry-After` seconds, or `RATE_LIMIT_ENABLED=false` in development |
| `python -m scripts.create_admin` says missing variables | set the four `ADMIN_*` values in `.env` |
| PowerShell won’t activate the venv | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
