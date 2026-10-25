from bson import ObjectId

from app.db.mongodb import Collections
from tests.conftest import PASSWORD, upload_note

MISSING_ID = str(ObjectId())


async def test_user_list_hides_secrets_and_supports_filters(admin, user, uploader):
    r = await admin.get("/api/admin/users")
    assert r.status_code == 200 and r.json()["total"] == 3
    assert "passwordHash" not in r.text and all("email" in u for u in r.json()["items"])
    assert (await admin.get("/api/admin/users", params={"role": "uploader"})).json()["total"] == 1
    assert (await admin.get("/api/admin/users", params={"q": "plain"})).json()["total"] == 1
    assert (await admin.get("/api/admin/users", params={"q": ".*"})).json()["total"] == 0  # regex-escaped
    assert (await admin.get("/api/admin/users", params={"role": "superuser"})).status_code == 422
    assert (await admin.get("/api/admin/users", params={"isActive": "false"})).json()["total"] == 0


async def test_user_detail_errors(admin, uploader, seed):
    assert (await admin.get("/api/admin/users/not-an-id")).status_code == 400
    assert (await admin.get(f"/api/admin/users/{MISSING_ID}")).status_code == 404
    await upload_note(uploader, seed)
    detail = await admin.get(f"/api/admin/users/{uploader.account['id']}")
    assert detail.status_code == 200 and detail.json()["noteCount"] == 1


async def test_admin_promotes_and_revokes_uploader(admin, user, seed, db):
    assert (await upload_note(user, seed)).status_code == 403
    r = await admin.patch(f"/api/admin/users/{user.account['id']}/role", json={"role": "uploader"})
    assert r.status_code == 200 and r.json()["role"] == "uploader"
    assert (await upload_note(user, seed)).status_code == 201  # takes effect immediately (role read per request)
    r = await admin.patch(f"/api/admin/users/{user.account['id']}/role", json={"role": "user"})
    assert r.json()["role"] == "user"
    assert (await upload_note(user, seed)).status_code == 403
    logs = [a async for a in db[Collections.AUDIT_LOGS].find({"action": "user.role_change"})]
    assert [(l["metadata"]["from"], l["metadata"]["to"]) for l in logs] == [("user", "uploader"), ("uploader", "user")]


async def test_role_change_validation(admin, user):
    uid = user.account["id"]
    assert (await admin.patch(f"/api/admin/users/{uid}/role", json={"role": "superuser"})).status_code == 422
    assert (await admin.patch(f"/api/admin/users/{uid}/role", json={"role": "user", "extra": 1})).status_code == 422
    assert (await admin.patch(f"/api/admin/users/{MISSING_ID}/role", json={"role": "user"})).status_code == 404
    assert (await admin.patch("/api/admin/users/bad/role", json={"role": "user"})).status_code == 400


async def test_last_admin_cannot_be_demoted_or_disabled(admin, user):
    me = admin.account["id"]
    r = await admin.patch(f"/api/admin/users/{me}/role", json={"role": "user"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "last_admin"
    assert (await admin.patch(f"/api/admin/users/{me}/status", json={"isActive": False})).status_code == 403
    # with a second admin, the first may step down
    await admin.patch(f"/api/admin/users/{user.account['id']}/role", json={"role": "admin"})
    assert (await admin.patch(f"/api/admin/users/{me}/role", json={"role": "user"})).status_code == 200
    # ...and now the remaining admin is protected
    r = await user.patch(f"/api/admin/users/{user.account['id']}/role", json={"role": "user"})
    assert r.status_code == 409


async def test_disabling_a_user_blocks_login_and_existing_sessions(admin, user, anon):
    uid = user.account["id"]
    assert (await user.get("/api/auth/me")).status_code == 200
    r = await admin.patch(f"/api/admin/users/{uid}/status", json={"isActive": False})
    assert r.status_code == 200 and r.json()["isActive"] is False
    me = await user.get("/api/auth/me")
    assert me.status_code == 403 and me.json()["error"]["code"] == "account_disabled"
    assert (await user.post("/api/auth/refresh")).status_code == 401
    login = await anon.post("/api/auth/login", json={"email": "plainuser@example.com", "password": PASSWORD})
    assert login.status_code == 403
    assert (await anon.get("/api/users/plainuser/public")).status_code == 404
    await admin.patch(f"/api/admin/users/{uid}/status", json={"isActive": True})
    assert (await anon.post("/api/auth/login", json={"email": "plainuser@example.com", "password": PASSWORD})).status_code == 200


async def test_dashboard_counts_and_recent_activity(admin, user, uploader, seed):
    await upload_note(uploader, seed)
    rid = (await user.post("/api/departments/requests", json={"name": "Biotech", "facultyId": seed["faculty_id"]})).json()["id"]
    await admin.patch(f"/api/admin/users/{user.account['id']}/role", json={"role": "uploader"})
    r = await admin.get("/api/admin/dashboard")
    assert r.status_code == 200
    c = r.json()["counts"]
    assert c == {"users": 3, "uploaders": 2, "admins": 1, "notes": 1, "publishedNotes": 1, "faculties": 2,
                 "departments": 2, "pendingDepartmentRequests": 1}
    activity = r.json()["recentActivity"]
    assert activity[0]["action"] == "user.role_change" and activity[0]["actorUsername"] == "adminuser"
    await admin.patch(f"/api/admin/department-requests/{rid}/reject")
    assert (await admin.get("/api/admin/dashboard")).json()["counts"]["pendingDepartmentRequests"] == 0


async def test_create_admin_script_is_safe_to_rerun(db, monkeypatch, capsys):
    from scripts import create_admin

    monkeypatch.setenv("ADMIN_NAME", "Root Admin")
    monkeypatch.setenv("ADMIN_USERNAME", "rootadmin")
    monkeypatch.setenv("ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", PASSWORD)
    assert await create_admin.run(promote=False) == 0
    assert await create_admin.run(promote=False) == 0  # second run: no duplicate
    assert await db[Collections.USERS].count_documents({"role": "admin"}) == 1
    out = capsys.readouterr().out
    assert "Administrator created" in out and "already exists" in out
