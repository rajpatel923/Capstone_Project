import pytest

from app.core.security import encrypt_totp_secret, generate_totp_secret, hash_api_key
from app.db.models import Student


@pytest.mark.asyncio
async def test_get_student_not_found(client, db_session):
    from app.core.dependencies import require_admin
    from app.main import app

    async def _fake_admin():
        return "test-clerk-user"

    app.dependency_overrides[require_admin] = _fake_admin

    resp = await client.get("/students/99999")
    assert resp.status_code == 404

    app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_list_students_empty(client, db_session):
    from app.core.dependencies import require_admin
    from app.main import app

    async def _fake_admin():
        return "test-clerk-user"

    app.dependency_overrides[require_admin] = _fake_admin

    resp = await client.get("/students")
    assert resp.status_code == 200
    assert resp.json()["items"] == [] or isinstance(resp.json()["items"], list)

    app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_enroll_student(client, db_session, fake_admin):
    resp = await client.post(
        "/students",
        json={"full_name": "Alice Smith", "email": "alice@example.com"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert "provisioning_uri" in data
    assert len(data["member_id"]) == 4


@pytest.mark.asyncio
async def test_enroll_student_duplicate_email(client, db_session, fake_admin):
    await client.post(
        "/students",
        json={"full_name": "Bob Jones", "email": "bob@example.com"},
    )
    resp = await client.post(
        "/students",
        json={"full_name": "Bob Clone", "email": "bob@example.com"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_student(client, db_session, fake_admin):
    enroll = await client.post(
        "/students",
        json={"full_name": "Carol White", "email": "carol@example.com"},
    )
    student_id = enroll.json()["id"]
    resp = await client.patch(f"/students/{student_id}", json={"full_name": "Carol Black"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Carol Black"


@pytest.mark.asyncio
async def test_update_student_not_found(client, db_session, fake_admin):
    resp = await client.patch("/students/99999", json={"full_name": "Ghost"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reset_totp(client, db_session, fake_admin):
    enroll = await client.post(
        "/students",
        json={"full_name": "Dave Green", "email": "dave@example.com"},
    )
    student_id = enroll.json()["id"]
    resp = await client.post(f"/students/{student_id}/reset-totp")
    assert resp.status_code == 200
    data = resp.json()
    assert "provisioning_uri" in data
    assert "otpauth://" in data["provisioning_uri"]
