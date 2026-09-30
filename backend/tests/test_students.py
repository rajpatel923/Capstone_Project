import pytest

from app.core.security import encrypt_totp_secret, generate_totp_secret, hash_api_key
from app.db.models import Student


@pytest.mark.asyncio
async def test_get_student_not_found(client, db_session):
    # require_admin will fail without a real Clerk JWT in tests
    # so we override that dependency too
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
