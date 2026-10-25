from bson import ObjectId

from app.db.mongodb import Collections
from tests.conftest import upload_note

BAD_ID = "bad"


async def new_note(uploader, seed, **kw) -> str:
    return (await upload_note(uploader, seed, **kw)).json()["id"]


async def test_saved_notes_require_login(anon, uploader, seed):
    nid = await new_note(uploader, seed)
    assert (await anon.get("/api/saved-notes")).status_code == 401
    assert (await anon.post(f"/api/saved-notes/{nid}")).status_code == 401
    assert (await anon.delete(f"/api/saved-notes/{nid}")).status_code == 401


async def test_save_is_idempotent_and_never_duplicates(user, uploader, seed, db):
    nid = await new_note(uploader, seed)
    first = await user.post(f"/api/saved-notes/{nid}")
    again = await user.post(f"/api/saved-notes/{nid}")
    assert first.status_code == 201 and again.status_code == 200
    assert first.json() == {"noteId": nid, "saved": True}
    assert await db[Collections.SAVED_NOTES].count_documents({"userId": ObjectId(user.account["id"])}) == 1


async def test_list_returns_note_details_for_the_caller_only(user, uploader, uploader2, seed):
    n1 = await new_note(uploader, seed, title="First Note")
    await new_note(uploader, seed, title="Unsaved Note")
    await user.post(f"/api/saved-notes/{n1}")
    r = await user.get("/api/saved-notes")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1 and body["items"][0]["note"]["title"] == "First Note"
    assert body["items"][0]["note"]["uploader"]["username"] == "uploader1" and body["items"][0]["savedAt"]
    assert (await uploader2.get("/api/saved-notes")).json()["total"] == 0  # others never see my collection


async def test_pagination_and_newest_first(user, uploader, seed):
    ids = [await new_note(uploader, seed, title=f"Note number {i}") for i in range(3)]
    for nid in ids:
        await user.post(f"/api/saved-notes/{nid}")
    page = (await user.get("/api/saved-notes", params={"limit": 2})).json()
    assert page["total"] == 3 and page["totalPages"] == 2
    assert page["items"][0]["note"]["id"] == ids[-1]
    assert (await user.get("/api/saved-notes", params={"limit": 2, "page": 2})).json()["items"][0]["note"]["id"] == ids[0]


async def test_unsave_is_idempotent(user, uploader, seed):
    nid = await new_note(uploader, seed)
    await user.post(f"/api/saved-notes/{nid}")
    assert (await user.delete(f"/api/saved-notes/{nid}")).json() == {"noteId": nid, "saved": False}
    assert (await user.delete(f"/api/saved-notes/{nid}")).status_code == 200
    assert (await user.get("/api/saved-notes")).json()["total"] == 0


async def test_invalid_missing_and_unpublished_notes(user, uploader, seed):
    assert (await user.post(f"/api/saved-notes/{BAD_ID}")).status_code == 400
    assert (await user.delete(f"/api/saved-notes/{BAD_ID}")).status_code == 400
    assert (await user.post(f"/api/saved-notes/{ObjectId()}")).status_code == 404
    nid = await new_note(uploader, seed)
    await uploader.patch(f"/api/notes/{nid}", json={"isPublished": False})
    assert (await user.post(f"/api/saved-notes/{nid}")).status_code == 404


async def test_notes_that_become_unpublished_or_deleted_leave_the_list(user, uploader, seed):
    a, b = await new_note(uploader, seed, title="Keep Me"), await new_note(uploader, seed, title="Hide Me")
    await user.post(f"/api/saved-notes/{a}")
    await user.post(f"/api/saved-notes/{b}")
    await uploader.patch(f"/api/notes/{b}", json={"isPublished": False})
    items = (await user.get("/api/saved-notes")).json()
    assert items["total"] == 1 and items["items"][0]["note"]["title"] == "Keep Me"
    await uploader.delete(f"/api/notes/{a}")
    assert (await user.get("/api/saved-notes")).json()["total"] == 0
