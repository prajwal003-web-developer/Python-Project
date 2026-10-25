from bson import ObjectId

from app.db.mongodb import Collections
from tests.conftest import upload_note

BAD_ID = "not-an-object-id"
MISSING_ID = str(ObjectId())


async def test_public_can_browse_faculties_and_departments(anon, seed):
    r = await anon.get("/api/faculties")
    assert r.status_code == 200 and {f["name"] for f in r.json()} == {"Engineering", "Science"}
    assert (await anon.get(f"/api/faculties/{seed['faculty_id']}")).json()["slug"] == "engineering"
    r = await anon.get("/api/departments", params={"facultyId": seed["faculty_id"]})
    assert [d["name"] for d in r.json()] == ["Computer Science"]
    assert (await anon.get(f"/api/departments/{seed['department_id']}")).status_code == 200


async def test_invalid_and_missing_ids(anon, seed):
    assert (await anon.get(f"/api/faculties/{BAD_ID}")).status_code == 400
    assert (await anon.get(f"/api/faculties/{MISSING_ID}")).status_code == 404
    assert (await anon.get(f"/api/departments/{BAD_ID}")).status_code == 400
    assert (await anon.get(f"/api/departments/{MISSING_ID}")).status_code == 404
    assert (await anon.get("/api/departments", params={"facultyId": BAD_ID})).status_code == 400


def req(seed, name="Biotechnology", **extra):
    return {"name": name, "facultyId": seed["faculty_id"], "description": "New programme", **extra}


async def test_department_request_requires_login(anon, seed):
    assert (await anon.post("/api/departments/requests", json=req(seed))).status_code == 401
    assert (await anon.get("/api/departments/requests/mine")).status_code == 401


async def test_user_creates_request_and_cannot_set_status(user, seed):
    r = await user.post("/api/departments/requests", json=req(seed))
    assert r.status_code == 201 and r.json()["status"] == "pending" and r.json()["slug"] == "biotechnology"
    assert (await user.post("/api/departments/requests", json=req(seed, "Other", status="approved"))).status_code == 422
    assert (await user.post("/api/departments/requests", json=req(seed, "Other", requestedBy=MISSING_ID))).status_code == 422
    mine = await user.get("/api/departments/requests/mine")
    assert mine.json()["total"] == 1


async def test_duplicate_requests_are_blocked(user, seed):
    assert (await user.post("/api/departments/requests", json=req(seed))).status_code == 201
    dup = await user.post("/api/departments/requests", json=req(seed, "BIOTECHNOLOGY"))
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "request_pending"
    existing = await user.post("/api/departments/requests", json=req(seed, "Computer Science"))
    assert existing.json()["error"]["code"] == "department_exists"
    bad_fac = await user.post("/api/departments/requests", json={**req(seed), "facultyId": MISSING_ID})
    assert bad_fac.status_code == 404


async def test_my_requests_only_shows_own(user, uploader, seed):
    await user.post("/api/departments/requests", json=req(seed, "Mine"))
    await uploader.post("/api/departments/requests", json=req(seed, "Theirs"))
    names = [i["name"] for i in (await user.get("/api/departments/requests/mine")).json()["items"]]
    assert names == ["Mine"]


async def test_admin_endpoints_reject_non_admins(anon, user, uploader, seed):
    paths = [("get", "/api/admin/department-requests"), ("post", "/api/admin/faculties"),
             ("get", "/api/admin/users"), ("get", "/api/admin/dashboard")]
    for method, path in paths:
        kw = {"json": {"name": "X Faculty"}} if method == "post" else {}
        assert (await getattr(anon, method)(path, **kw)).status_code == 401
        assert (await getattr(user, method)(path, **kw)).status_code == 403
        assert (await getattr(uploader, method)(path, **kw)).status_code == 403


async def test_admin_approves_request_and_department_appears(user, admin, anon, seed):
    rid = (await user.post("/api/departments/requests", json=req(seed))).json()["id"]
    listing = await admin.get("/api/admin/department-requests", params={"status": "pending"})
    assert listing.json()["total"] == 1 and listing.json()["items"][0]["requesterUsername"] == "plainuser"
    r = await admin.patch(f"/api/admin/department-requests/{rid}/approve", json={"adminComment": "Welcome"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved" and body["adminComment"] == "Welcome" and body["departmentId"]
    depts = (await anon.get("/api/departments", params={"facultyId": seed["faculty_id"]})).json()
    assert "Biotechnology" in {d["name"] for d in depts}
    again = await admin.patch(f"/api/admin/department-requests/{rid}/approve")
    assert again.status_code == 409 and again.json()["error"]["code"] == "request_already_reviewed"
    assert (await admin.patch(f"/api/admin/department-requests/{rid}/reject")).status_code == 409


async def test_admin_rejects_request_and_history_is_kept(user, admin, anon, seed, db):
    rid = (await user.post("/api/departments/requests", json=req(seed))).json()["id"]
    r = await admin.patch(f"/api/admin/department-requests/{rid}/reject", json={"adminComment": "Duplicate"})
    assert r.status_code == 200 and r.json()["status"] == "rejected" and r.json()["reviewedBy"]
    assert (await db[Collections.DEPARTMENT_REQUESTS].count_documents({})) == 1
    names = {d["name"] for d in (await anon.get("/api/departments")).json()}
    assert "Biotechnology" not in names
    assert (await user.post("/api/departments/requests", json=req(seed))).status_code == 201  # may re-request


async def test_approval_with_existing_department_rolls_back_to_pending(user, admin, seed, db):
    rid = (await user.post("/api/departments/requests", json=req(seed))).json()["id"]
    await admin.post("/api/admin/departments", json={"name": "Biotechnology", "facultyId": seed["faculty_id"]})
    r = await admin.patch(f"/api/admin/department-requests/{rid}/approve")
    assert r.status_code == 409 and r.json()["error"]["code"] == "department_exists"
    assert (await admin.get(f"/api/admin/department-requests/{rid}")).json()["status"] == "pending"


async def test_request_lookup_errors(admin):
    assert (await admin.get(f"/api/admin/department-requests/{BAD_ID}")).status_code == 400
    assert (await admin.get(f"/api/admin/department-requests/{MISSING_ID}")).status_code == 404
    assert (await admin.patch(f"/api/admin/department-requests/{MISSING_ID}/approve")).status_code == 404


async def test_admin_faculty_and_department_crud(admin, anon, seed):
    f = await admin.post("/api/admin/faculties", json={"name": "Law & Policy", "description": "Legal studies"})
    assert f.status_code == 201 and f.json()["slug"] == "law-policy"
    assert (await admin.post("/api/admin/faculties", json={"name": "law policy"})).status_code == 409
    fid = f.json()["id"]
    assert (await admin.patch(f"/api/admin/faculties/{fid}", json={"description": "Updated"})).json()["description"] == "Updated"
    d = await admin.post("/api/admin/departments", json={"name": "Criminal Law", "facultyId": fid})
    assert d.status_code == 201
    did = d.json()["id"]
    assert (await admin.post("/api/admin/departments", json={"name": "Criminal Law", "facultyId": fid})).status_code == 409
    # faculty with an active department cannot be deleted
    blocked = await admin.delete(f"/api/admin/faculties/{fid}")
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "faculty_has_departments"
    assert (await admin.delete(f"/api/admin/departments/{did}")).status_code == 200
    assert (await admin.delete(f"/api/admin/faculties/{fid}")).status_code == 200
    assert fid not in {x["id"] for x in (await anon.get("/api/faculties")).json()}
    assert (await anon.get(f"/api/faculties/{fid}")).status_code == 404  # soft deleted => hidden


async def test_cannot_delete_department_or_faculty_that_still_has_notes(admin, uploader, seed):
    assert (await upload_note(uploader, seed)).status_code == 201
    r = await admin.delete(f"/api/admin/departments/{seed['department_id']}")
    assert r.status_code == 409 and r.json()["error"]["code"] == "department_has_notes"
    deact = await admin.patch(f"/api/admin/departments/{seed['department_id']}", json={"isActive": False})
    assert deact.status_code == 409
    r = await admin.delete(f"/api/admin/faculties/{seed['faculty_id']}")
    assert r.status_code == 409


async def test_admin_actions_are_audited(user, admin, seed, db):
    rid = (await user.post("/api/departments/requests", json=req(seed))).json()["id"]
    await admin.patch(f"/api/admin/department-requests/{rid}/approve")
    await admin.post("/api/admin/faculties", json={"name": "Arts"})
    actions = {a["action"] async for a in db[Collections.AUDIT_LOGS].find()}
    assert {"department_request.approve", "faculty.create"} <= actions
