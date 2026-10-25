import pytest
from bson import ObjectId

from app.core.config import get_settings
from app.db.mongodb import Collections
from app.services import notes_service
from tests.conftest import DOCX_MIME, PDF_BYTES, make_docx_bytes, upload_note

BAD_ID = "xyz"
MISSING_ID = str(ObjectId())


# ------------------------------------------------------------------ uploading
async def test_anonymous_and_plain_user_cannot_upload(anon, user, seed, cloud):
    assert (await upload_note(anon, seed)).status_code == 401
    r = await upload_note(user, seed)
    assert r.status_code == 403 and r.json()["error"]["code"] == "uploader_required"
    assert cloud.uploaded == []


async def test_uploader_can_upload_pdf_and_docx(uploader, seed, cloud, db):
    r = await upload_note(uploader, seed)
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["fileType"] == "pdf" and note["uploader"] == {"name": "Uploader1", "username": "uploader1"}
    assert note["facultyName"] == "Engineering" and note["departmentName"] == "Computer Science" and note["semester"] == 3
    assert "publicId" not in r.text and "email" not in r.text and "passwordHash" not in r.text
    stored = await db[Collections.NOTES].find_one({"_id": ObjectId(note["id"])})
    assert stored["publicId"] in cloud.uploaded and stored["fileSize"] == len(PDF_BYTES)
    d = await upload_note(uploader, seed, title="Word Notes",
                          file=("notes.docx", make_docx_bytes(), DOCX_MIME))
    assert d.status_code == 201 and d.json()["fileType"] == "docx"


async def test_client_cannot_spoof_owner_or_role(uploader, uploader2, seed):
    r = await upload_note(uploader, seed, uploadedBy=uploader2.account["id"], role="admin")
    assert r.status_code == 201 and r.json()["uploader"]["username"] == "uploader1"


@pytest.mark.parametrize("filename,content,ctype,status,code", [
    ("notes.txt", b"hello", "text/plain", 415, "unsupported_file_type"),
    ("notes.exe", b"MZ", "application/octet-stream", 415, "unsupported_file_type"),
    ("fake.pdf", b"MZ this is not a pdf", "application/pdf", 415, "invalid_pdf"),
    ("fake.docx", b"PK\x03\x04garbage", DOCX_MIME, 415, "invalid_docx"),
    ("empty.pdf", b"", "application/pdf", 400, "empty_file"),
    ("mismatch.pdf", PDF_BYTES, "image/png", 415, "mime_mismatch"),
])
async def test_file_validation_failures(uploader, seed, cloud, filename, content, ctype, status, code):
    r = await upload_note(uploader, seed, file=(filename, content, ctype))
    assert r.status_code == status and r.json()["error"]["code"] == code
    assert cloud.uploaded == []  # nothing reaches Cloudinary


async def test_oversized_file_rejected(uploader, seed, cloud):
    big = b"%PDF-" + b"0" * (get_settings().max_upload_size_bytes + 10)
    r = await upload_note(uploader, seed, file=("big.pdf", big, "application/pdf"))
    assert r.status_code == 413 and cloud.uploaded == []


async def test_missing_file_and_bad_metadata(uploader, seed):
    r = await uploader.post("/api/notes", data={"title": "T" * 5, "subject": "DSA", "semester": "3",
                            "facultyId": seed["faculty_id"], "departmentId": seed["department_id"]})
    assert r.status_code == 422
    assert (await upload_note(uploader, seed, semester=9)).status_code == 422
    assert (await upload_note(uploader, seed, semester=0)).status_code == 422
    assert (await upload_note(uploader, seed, title="x")).status_code == 422
    assert (await upload_note(uploader, seed, facultyId=BAD_ID)).status_code == 400
    assert (await upload_note(uploader, seed, facultyId=MISSING_ID)).status_code == 404
    mismatch = await upload_note(uploader, seed, departmentId=seed["department2_id"])  # Physics is not in Engineering
    assert mismatch.status_code == 404 and mismatch.json()["error"]["code"] == "department_not_found"


async def test_failed_database_save_deletes_the_uploaded_asset(uploader, seed, cloud, db, monkeypatch):
    first = await upload_note(uploader, seed)
    existing_id = ObjectId(first.json()["id"])
    original = notes_service.build_note_document

    def colliding(**kw):  # force insert_one to fail with a duplicate _id
        doc = original(**kw)
        doc["_id"] = existing_id
        return doc

    monkeypatch.setattr(notes_service, "build_note_document", colliding)
    r = await upload_note(uploader, seed, title="Second Upload")
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert len(cloud.uploaded) == 2 and cloud.deleted == [cloud.uploaded[1]]  # compensation ran
    assert await db[Collections.NOTES].count_documents({}) == 1


# ------------------------------------------------------------------ public browsing
async def make_library(uploader, uploader2, seed):
    await upload_note(uploader, seed, title="Algorithms Handbook", subject="Algorithms", semester=3, description="sorting")
    await upload_note(uploader, seed, title="Operating Systems", subject="OS", semester=4,
                      file=("os.docx", make_docx_bytes(), DOCX_MIME))
    await upload_note(uploader2, seed, title="Quantum Basics", subject="Physics", semester=1,
                      facultyId=seed["faculty2_id"], departmentId=seed["department2_id"], description="100% .* literal")


async def test_public_browsing_without_login(anon, uploader, uploader2, seed):
    await make_library(uploader, uploader2, seed)
    r = await anon.get("/api/notes")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"items", "page", "limit", "total", "totalPages"} and body["total"] == 3
    assert all("email" not in n["uploader"] for n in body["items"])
    note_id = body["items"][0]["id"]
    assert (await anon.get(f"/api/notes/{note_id}")).status_code == 200
    assert (await anon.get(f"/api/notes/{BAD_ID}")).status_code == 400
    assert (await anon.get(f"/api/notes/{MISSING_ID}")).status_code == 404


async def test_search_filters_pagination_and_sorting(anon, uploader, uploader2, seed):
    await make_library(uploader, uploader2, seed)
    get = lambda **p: anon.get("/api/notes", params=p)  # noqa: E731
    assert (await get(q="algorithms")).json()["total"] == 1
    assert (await get(q="sorting")).json()["total"] == 1                      # matches description
    assert (await get(q="OS")).json()["items"][0]["title"] == "Operating Systems"  # matches subject (case-insens.)
    assert (await get(semester=3)).json()["total"] == 1
    assert (await get(fileType="docx")).json()["total"] == 1
    assert (await get(facultyId=seed["faculty2_id"])).json()["total"] == 1
    assert (await get(departmentId=seed["department_id"])).json()["total"] == 2
    assert (await get(username="UPLOADER2")).json()["total"] == 1
    assert (await get(username="ghost")).json()["total"] == 0
    p1 = (await get(limit=2, page=1, sortBy="title", sortOrder="asc")).json()
    assert p1["totalPages"] == 2 and [n["title"] for n in p1["items"]] == ["Algorithms Handbook", "Operating Systems"]
    p2 = (await get(limit=2, page=2, sortBy="title", sortOrder="asc")).json()
    assert [n["title"] for n in p2["items"]] == ["Quantum Basics"]


async def test_query_validation_and_injection_safety(anon, uploader, uploader2, seed):
    await make_library(uploader, uploader2, seed)
    assert (await anon.get("/api/notes", params={"limit": 500})).status_code == 422
    assert (await anon.get("/api/notes", params={"page": 0})).status_code == 422
    assert (await anon.get("/api/notes", params={"sortBy": "passwordHash"})).status_code == 422
    assert (await anon.get("/api/notes", params={"fileType": "exe"})).status_code == 422
    assert (await anon.get("/api/notes", params={"semester": "abc"})).status_code == 422
    assert (await anon.get("/api/notes", params={"facultyId": BAD_ID})).status_code == 400
    # regex metacharacters are literal text, not a pattern
    assert (await anon.get("/api/notes", params={"q": ".*"})).json()["total"] == 1
    assert (await anon.get("/api/notes", params={"q": "^Alg"})).json()["total"] == 0
    # operator-style parameters are ignored rather than forwarded to MongoDB
    r = await anon.get("/api/notes", params={"q[$ne]": "x", "username[$ne]": "x"})
    assert r.status_code == 200 and r.json()["total"] == 3


async def test_unpublished_notes_are_hidden_from_public(anon, uploader, admin, seed):
    nid = (await upload_note(uploader, seed)).json()["id"]
    assert (await uploader.patch(f"/api/notes/{nid}", json={"isPublished": False})).status_code == 200
    assert (await anon.get("/api/notes")).json()["total"] == 0
    assert (await anon.get(f"/api/notes/{nid}")).status_code == 404
    assert (await uploader.get(f"/api/notes/{nid}")).status_code == 200  # owner can still see it
    assert (await admin.get(f"/api/notes/{nid}")).status_code == 200
    assert (await anon.get("/api/users/uploader1/public")).json()["publicUploadCount"] == 0


# ------------------------------------------------------------------ public profiles
async def test_public_profile_and_user_notes(anon, uploader, uploader2, seed):
    await make_library(uploader, uploader2, seed)
    r = await anon.get("/api/users/uploader1/public", params={"limit": 1})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"name", "username", "publicUploadCount", "notes"}
    assert body["publicUploadCount"] == 2 and body["notes"]["total"] == 2 and len(body["notes"]["items"]) == 1
    assert "email" not in r.text and "role" not in r.text
    n = (await anon.get("/api/users/Uploader2/notes")).json()
    assert n["total"] == 1 and n["items"][0]["uploader"]["username"] == "uploader2"
    assert (await anon.get("/api/users/ghost/public")).status_code == 404
    assert (await anon.get("/api/users/ghost/notes")).status_code == 404


# ------------------------------------------------------------------ ownership
async def test_only_owner_can_edit_replace_or_delete(uploader, uploader2, user, anon, seed):
    nid = (await upload_note(uploader, seed)).json()["id"]
    for client in (uploader2,):
        assert (await client.patch(f"/api/notes/{nid}", json={"title": "Hijacked"})).status_code == 403
        assert (await client.put(f"/api/notes/{nid}/file", files={"file": ("a.pdf", PDF_BYTES, "application/pdf")})).status_code == 403
        assert (await client.delete(f"/api/notes/{nid}")).status_code == 403
    assert (await user.delete(f"/api/notes/{nid}")).status_code == 403
    assert (await anon.delete(f"/api/notes/{nid}")).status_code == 401
    assert (await anon.get(f"/api/notes/{nid}")).json()["title"] == "Data Structures Notes"


async def test_owner_updates_metadata_with_validation(uploader, seed):
    nid = (await upload_note(uploader, seed)).json()["id"]
    r = await uploader.patch(f"/api/notes/{nid}", json={"title": "Better Title", "semester": 5, "subject": "Graphs"})
    assert r.status_code == 200 and r.json()["title"] == "Better Title" and r.json()["semester"] == 5
    for bad in ({"uploadedBy": MISSING_ID}, {"fileUrl": "http://evil"}, {"role": "admin"}, {}):
        assert (await uploader.patch(f"/api/notes/{nid}", json=bad)).status_code == 422
    assert (await uploader.patch(f"/api/notes/{nid}", json={"semester": 99})).status_code == 422
    move = await uploader.patch(f"/api/notes/{nid}", json={"facultyId": seed["faculty2_id"],
                                                          "departmentId": seed["department2_id"]})
    assert move.status_code == 200 and move.json()["departmentName"] == "Physics"
    broken = await uploader.patch(f"/api/notes/{nid}", json={"departmentId": seed["department_id"]})
    assert broken.status_code == 404  # department no longer matches the (physics) faculty
    assert (await uploader.patch(f"/api/notes/{MISSING_ID}", json={"title": "Ghost note"})).status_code == 404


async def test_replace_file_swaps_asset_and_deletes_old_one(uploader, seed, cloud, db):
    nid = (await upload_note(uploader, seed)).json()["id"]
    old_pid = cloud.uploaded[0]
    r = await uploader.put(f"/api/notes/{nid}/file", files={"file": ("new.docx", make_docx_bytes(), DOCX_MIME)})
    assert r.status_code == 200 and r.json()["fileType"] == "docx"
    stored = await db[Collections.NOTES].find_one({"_id": ObjectId(nid)})
    assert stored["publicId"] == cloud.uploaded[1] != old_pid and cloud.deleted == [old_pid]


async def test_failed_replacement_keeps_existing_file(uploader, seed, cloud, db):
    nid = (await upload_note(uploader, seed)).json()["id"]
    before = (await db[Collections.NOTES].find_one({"_id": ObjectId(nid)}))["publicId"]
    r = await uploader.put(f"/api/notes/{nid}/file", files={"file": ("bad.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 415
    assert (await db[Collections.NOTES].find_one({"_id": ObjectId(nid)}))["publicId"] == before
    assert cloud.deleted == [] and len(cloud.uploaded) == 1


async def test_owner_delete_removes_note_asset_and_saved_references(uploader, user, seed, cloud, db):
    nid = (await upload_note(uploader, seed)).json()["id"]
    assert (await user.post(f"/api/saved-notes/{nid}")).status_code == 201
    r = await uploader.delete(f"/api/notes/{nid}")
    assert r.status_code == 200
    assert await db[Collections.NOTES].count_documents({}) == 0
    assert await db[Collections.SAVED_NOTES].count_documents({}) == 0
    assert cloud.deleted == [cloud.uploaded[0]]
    assert (await uploader.delete(f"/api/notes/{nid}")).status_code == 404


async def test_admin_moderation_is_limited_and_audited(uploader, admin, seed, db):
    nid = (await upload_note(uploader, seed)).json()["id"]
    assert (await admin.patch(f"/api/notes/{nid}", json={"title": "Admin edit"})).status_code == 403
    hide = await admin.patch(f"/api/notes/{nid}", json={"isPublished": False})
    assert hide.status_code == 200 and hide.json()["isPublished"] is False and hide.json()["hiddenByAdmin"] is True
    again = await uploader.patch(f"/api/notes/{nid}", json={"isPublished": True})
    assert again.status_code == 403 and again.json()["error"]["code"] == "hidden_by_admin"
    assert (await admin.patch(f"/api/notes/{nid}", json={"isPublished": True})).json()["isPublished"] is True
    assert await db[Collections.AUDIT_LOGS].count_documents({"action": "note.moderate"}) == 2


async def test_admin_can_delete_any_note_and_it_is_audited(uploader, admin, seed, db, cloud):
    nid = (await upload_note(uploader, seed)).json()["id"]
    assert (await admin.delete(f"/api/notes/{nid}")).status_code == 200
    assert await db[Collections.AUDIT_LOGS].count_documents({"action": "note.delete_by_admin"}) == 1
    assert cloud.deleted == [cloud.uploaded[0]]


async def test_revoked_uploader_cannot_edit_but_can_delete_own(uploader, admin, seed):
    nid = (await upload_note(uploader, seed)).json()["id"]
    await admin.patch(f"/api/admin/users/{uploader.account['id']}/role", json={"role": "user"})
    assert (await upload_note(uploader, seed)).status_code == 403
    assert (await uploader.patch(f"/api/notes/{nid}", json={"title": "Still editing"})).status_code == 403
    assert (await uploader.delete(f"/api/notes/{nid}")).status_code == 200


# ------------------------------------------------------------------ uploader dashboard
async def test_my_notes_statistics_and_access_control(uploader, uploader2, user, anon, seed):
    assert (await anon.get("/api/notes/mine")).status_code == 401
    assert (await user.get("/api/notes/mine")).status_code == 403
    await make_library(uploader, uploader2, seed)
    hidden = (await upload_note(uploader, seed, title="Draft Notes")).json()["id"]
    await uploader.patch(f"/api/notes/{hidden}", json={"isPublished": False})
    r = await uploader.get("/api/notes/mine")
    assert r.status_code == 200
    stats, notes = r.json()["stats"], r.json()["notes"]
    assert stats["totalNotes"] == 3 and stats["publishedNotes"] == 2 and stats["unpublishedNotes"] == 1
    assert stats["pdfCount"] == 2 and stats["docxCount"] == 1 and stats["totalFileSize"] > 0
    assert stats["lastUploadedAt"] and stats["firstUploadedAt"]
    assert notes["total"] == 3 and all(n["uploader"]["username"] == "uploader1" for n in notes["items"])
    assert (await uploader.get("/api/notes/mine", params={"q": "draft"})).json()["notes"]["total"] == 1
    assert (await uploader.get("/api/notes/mine", params={"sortBy": "bogus"})).status_code == 422
