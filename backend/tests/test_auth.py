from app.core.config import get_settings
from app.core.rate_limit import login_limiter
from app.db.mongodb import Collections
from tests.conftest import PASSWORD, create_account

REG = {"name": "Alice Doe", "username": "alice", "email": "Alice@Example.com",
       "password": PASSWORD, "confirmPassword": PASSWORD}


async def test_register_creates_user_role_and_hashes_password(anon, db):
    r = await anon.post("/api/auth/register", json={**REG, "role": "admin", "isActive": False})
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "user" and body["email"] == "alice@example.com"
    assert "passwordHash" not in r.text and PASSWORD not in r.text
    stored = await db[Collections.USERS].find_one({"normalizedUsername": "alice"})
    assert stored["role"] == "user" and stored["passwordHash"].startswith("$argon2") and stored["passwordHash"] != PASSWORD


async def test_duplicate_email_and_username_are_rejected_case_insensitively(anon):
    assert (await anon.post("/api/auth/register", json=REG)).status_code == 201
    dup_email = await anon.post("/api/auth/register", json={**REG, "username": "other", "email": "ALICE@example.com"})
    assert dup_email.status_code == 409
    assert dup_email.json()["error"]["details"][0]["field"] == "email"
    dup_name = await anon.post("/api/auth/register", json={**REG, "username": "ALICE", "email": "new@example.com"})
    assert dup_name.status_code == 409
    assert dup_name.json()["error"]["details"][0]["field"] == "username"


async def test_registration_validation(anon):
    for patch in ({"password": "short"}, {"password": "alllowercase1"}, {"confirmPassword": "Different1Pass"},
                  {"email": "not-an-email"}, {"username": "a b"}, {"username": "admin"}):
        r = await anon.post("/api/auth/register", json={**REG, **patch})
        assert r.status_code == 422, patch
        assert r.json()["error"]["code"] == "validation_error"


async def test_login_sets_cookies_and_returns_safe_user(anon):
    await anon.post("/api/auth/register", json=REG)
    r = await anon.post("/api/auth/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["username"] == "alice" and data["csrfToken"]
    assert "passwordHash" not in r.text
    cookies = r.headers.get_list("set-cookie")
    assert any(c.startswith("access_token=") and "HttpOnly" in c for c in cookies)
    assert any(c.startswith("refresh_token=") and "HttpOnly" in c and "Path=/api/auth" in c for c in cookies)
    assert "access_token" not in r.text.replace("accessToken", "")  # tokens are never in the body


async def test_invalid_credentials_do_not_reveal_which_part_was_wrong(anon):
    await anon.post("/api/auth/register", json=REG)
    wrong_pw = await anon.post("/api/auth/login", json={"email": "alice@example.com", "password": "Wrong1Password"})
    unknown = await anon.post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


async def test_me_requires_login_and_hides_secrets(anon, user):
    assert (await anon.get("/api/auth/me")).status_code == 401
    r = await user.get("/api/auth/me")
    assert r.status_code == 200 and r.json()["username"] == "plainuser" and "passwordHash" not in r.text


async def test_profile_update_cannot_escalate_privileges(user, db):
    for field in ({"role": "admin"}, {"isActive": False}, {"email": "x@y.com"}):
        assert (await user.patch("/api/auth/me", json=field)).status_code == 422
    r = await user.patch("/api/auth/me", json={"name": "New Name", "username": "renamed"})
    assert r.status_code == 200 and r.json()["name"] == "New Name" and r.json()["username"] == "renamed"
    assert (await db[Collections.USERS].find_one({"normalizedUsername": "renamed"}))["role"] == "user"


async def test_password_change_requires_current_password_and_invalidates_old(user, anon):
    bad = await user.patch("/api/auth/me", json={"currentPassword": "Wrong1Password", "newPassword": "NewStr0ngPass1"})
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_current_password"
    ok = await user.patch("/api/auth/me", json={"currentPassword": PASSWORD, "newPassword": "NewStr0ngPass1"})
    assert ok.status_code == 200
    assert (await user.get("/api/auth/me")).status_code == 200  # this device stays signed in
    old = await anon.post("/api/auth/login", json={"email": "plainuser@example.com", "password": PASSWORD})
    assert old.status_code == 401
    new = await anon.post("/api/auth/login", json={"email": "plainuser@example.com", "password": "NewStr0ngPass1"})
    assert new.status_code == 200


async def test_state_changing_requests_need_csrf_header(user):
    token = user.headers.pop("X-CSRF-Token")
    r = await user.patch("/api/auth/me", json={"name": "Blocked Name"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "csrf_failed"
    user.headers["X-CSRF-Token"] = token
    assert (await user.patch("/api/auth/me", json={"name": "Allowed Name"})).status_code == 200
    r = await user.patch("/api/auth/me", json={"name": "Evil Origin"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


async def test_refresh_rotates_and_reuse_is_detected(user, client_factory):
    jar = {c.name: c for c in user.cookies.jar}
    old_refresh = jar["refresh_token"].value
    r = await user.post("/api/auth/refresh")
    assert r.status_code == 200 and r.json()["user"]["username"] == "plainuser"
    new_refresh = {c.name: c.value for c in user.cookies.jar}["refresh_token"]
    assert new_refresh != old_refresh
    for c in user.cookies.jar:  # replay the already-used refresh token
        if c.name == "refresh_token":
            c.value = old_refresh
    replay = await user.post("/api/auth/refresh")
    assert replay.status_code == 401 and replay.json()["error"]["code"] == "token_reuse_detected"
    for c in user.cookies.jar:  # the legitimately-issued newer token is revoked too (family revoked)
        if c.name == "refresh_token":
            c.value = new_refresh
    assert (await user.post("/api/auth/refresh")).status_code == 401


async def test_logout_revokes_session(user):
    assert (await user.post("/api/auth/logout")).status_code == 200
    assert (await user.get("/api/auth/me")).status_code == 401
    assert (await user.post("/api/auth/refresh")).status_code == 401


async def test_login_is_rate_limited(anon, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "login_rate_limit", 3)
    login_limiter.reset()
    codes = [(await anon.post("/api/auth/login", json={"email": "a@b.com", "password": "x"})).status_code
             for _ in range(4)]
    assert codes == [401, 401, 401, 429]


async def test_disabled_account_cannot_login(anon, db):
    await create_account(anon, db, username="soonoff")
    await db[Collections.USERS].update_one({"normalizedUsername": "soonoff"}, {"$set": {"isActive": False}})
    r = await anon.post("/api/auth/login", json={"email": "soonoff@example.com", "password": PASSWORD})
    assert r.status_code == 403 and r.json()["error"]["code"] == "account_disabled"
