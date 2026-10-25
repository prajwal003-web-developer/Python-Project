"""Test harness.

SAFETY: tests NEVER use your .env database. They connect to TEST_MONGODB_URL (default
mongodb://localhost:27017) and a throw-away database that is dropped when the run ends.
Cloudinary is replaced by an in-memory fake, so no credentials are needed.
"""
import io
import os
import uuid
import zipfile
from dataclasses import dataclass, field

# Must be set BEFORE any `app` import (settings are cached). Explicit assignment, not setdefault,
# so a developer's real .env / shell variables can never leak into the test run.
os.environ["MONGODB_URL"] = os.environ.get("TEST_MONGODB_URL", "mongodb://localhost:27017")
os.environ["MONGODB_DB_NAME"] = f"adtu_notes_test_{uuid.uuid4().hex[:8]}"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-" + "x" * 40
os.environ["ENVIRONMENT"] = "testing"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["COOKIE_SECURE"] = "false"
os.environ["COOKIE_SAMESITE"] = "lax"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["MAX_UPLOAD_SIZE_MB"] = "5"

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.rate_limit import ALL_LIMITERS  # noqa: E402
from app.db.indexes import create_indexes  # noqa: E402
from app.db.mongodb import Collections, mongo  # noqa: E402
from app.main import app  # noqa: E402
from app.models.department import build_department_document  # noqa: E402
from app.models.faculty import build_faculty_document  # noqa: E402
from app.services import cloudinary_service  # noqa: E402
from app.services.cloudinary_service import UploadedAsset  # noqa: E402
from app.utils.serialization import utcnow  # noqa: E402

PASSWORD = "Str0ngPassw0rd"
PDF_BYTES = b"%PDF-1.4\n%test document\n%%EOF\n"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def make_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


# ---------------------------------------------------------------- database
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def database():
    settings = get_settings()
    assert "_test_" in settings.mongodb_db_name
    await mongo.connect(settings)
    db = mongo.database
    await create_indexes(db)
    yield db
    await mongo._client.drop_database(settings.mongodb_db_name)
    await mongo.close()


@pytest_asyncio.fixture(autouse=True)
async def _clean(database, cloud):
    for name in vars(Collections).values():
        if isinstance(name, str) and not name.startswith("_"):
            await database[name].delete_many({})
    for limiter in ALL_LIMITERS:
        limiter.reset()
    cloud.uploaded.clear()
    cloud.deleted.clear()


@pytest.fixture
def db(database):
    return database


# ---------------------------------------------------------------- fake Cloudinary
@dataclass
class FakeCloud:
    uploaded: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


@pytest.fixture(autouse=True)
def cloud(monkeypatch) -> FakeCloud:
    fake = FakeCloud()

    async def upload(file):
        pid = f"test-folder/{uuid.uuid4().hex}-{file.safe_stem}.{file.file_type}"
        fake.uploaded.append(pid)
        return UploadedAsset(url=f"https://res.cloudinary.test/raw/upload/{pid}", public_id=pid, size=file.size)

    async def delete(public_id):
        fake.deleted.append(public_id)

    monkeypatch.setattr(cloudinary_service, "upload_note_file", upload)
    monkeypatch.setattr(cloudinary_service, "delete_asset", delete)
    return fake


# ---------------------------------------------------------------- HTTP clients
@pytest_asyncio.fixture
async def client_factory(database):
    clients: list[httpx.AsyncClient] = []

    def make() -> httpx.AsyncClient:
        # raise_app_exceptions=False: unhandled errors come back as a real HTTP 500, like in production
        c = httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                              base_url="http://test")
        clients.append(c)
        return c

    yield make
    for c in clients:
        await c.aclose()


@pytest.fixture
def anon(client_factory):
    return client_factory()


async def create_account(client, db, *, username: str, role: str = "user") -> dict:
    """Registers via the API, optionally sets the role directly in the DB, logs in, arms CSRF header."""
    email = f"{username}@example.com"
    r = await client.post("/api/auth/register", json={
        "name": username.title(), "username": username, "email": email,
        "password": PASSWORD, "confirmPassword": PASSWORD})
    assert r.status_code == 201, r.text
    if role != "user":
        await db[Collections.USERS].update_one({"normalizedUsername": username.lower()}, {"$set": {"role": role}})
    r = await client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrfToken"]
    client.account = r.json()["user"]
    return r.json()["user"]


@pytest_asyncio.fixture
async def user(client_factory, db):
    c = client_factory()
    await create_account(c, db, username="plainuser")
    return c


@pytest_asyncio.fixture
async def uploader(client_factory, db):
    c = client_factory()
    await create_account(c, db, username="uploader1", role="uploader")
    return c


@pytest_asyncio.fixture
async def uploader2(client_factory, db):
    c = client_factory()
    await create_account(c, db, username="uploader2", role="uploader")
    return c


@pytest_asyncio.fixture
async def admin(client_factory, db):
    c = client_factory()
    await create_account(c, db, username="adminuser", role="admin")
    return c


# ---------------------------------------------------------------- seed data / helpers
@pytest_asyncio.fixture
async def seed(db) -> dict:
    now = utcnow()
    fac = build_faculty_document(name="Engineering", slug="engineering", description="", now=now)
    fac2 = build_faculty_document(name="Science", slug="science", description="", now=now)
    await db[Collections.FACULTIES].insert_many([fac, fac2])
    dep = build_department_document(name="Computer Science", slug="computer-science", faculty_id=fac["_id"],
                                    description="", now=now)
    dep2 = build_department_document(name="Physics", slug="physics", faculty_id=fac2["_id"], description="", now=now)
    await db[Collections.DEPARTMENTS].insert_many([dep, dep2])
    return {"faculty_id": str(fac["_id"]), "department_id": str(dep["_id"]),
            "faculty2_id": str(fac2["_id"]), "department2_id": str(dep2["_id"])}


async def upload_note(client, seed, *, title="Data Structures Notes", subject="DSA", semester=3,
                      description="Trees and graphs", file=None, **overrides):
    data = {"title": title, "subject": subject, "semester": str(semester), "description": description,
            "facultyId": seed["faculty_id"], "departmentId": seed["department_id"], **overrides}
    return await client.post("/api/notes", data=data,
                             files={"file": file or ("notes.pdf", PDF_BYTES, "application/pdf")})
