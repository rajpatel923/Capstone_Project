"""Tests for student enrollment with admin-chosen member_id."""
import pytest

from app.core.dependencies import require_admin
from app.main import app


@pytest.fixture(autouse=True)
def override_admin():
    async def _fake_admin():
        return "test-admin"

    app.dependency_overrides[require_admin] = _fake_admin
    yield
    app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_enroll_student_with_member_id(client, db_session):
    resp = await client.post(
        "/students",
        json={"member_id": "1234", "full_name": "Alice Tester", "email": "alice@example.com"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["member_id"] == "1234"
    assert "totp_provisioning_uri" in data
    assert data["totp_provisioning_uri"].startswith("otpauth://")


@pytest.mark.asyncio
async def test_enroll_duplicate_member_id(client, db_session):
    # First enrollment — use a unique member_id for this test
    r1 = await client.post(
        "/students",
        json={"member_id": "2345", "full_name": "Alice Dup", "email": "alice-dup@example.com"},
    )
    assert r1.status_code == 201, r1.text

    # Second enrollment with same member_id
    r2 = await client.post(
        "/students",
        json={"member_id": "2345", "full_name": "Bob Tester", "email": "bob-dup@example.com"},
    )
    assert r2.status_code == 409
    assert "member_id" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_invalid_member_id(client, db_session):
    resp = await client.post(
        "/students",
        json={"member_id": "12A4", "full_name": "Bad Actor", "email": "bad@example.com"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_students_has_credit_and_eligibility(client, db_session):
    # Enroll a fresh student with a unique member_id
    await client.post(
        "/students",
        json={"member_id": "9998", "full_name": "List Tester", "email": "list-unique@example.com"},
    )

    resp = await client.get("/students")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    # Find our student
    matching = [s for s in items if s["member_id"] == "9998"]
    assert len(matching) == 1
    s = matching[0]
    assert s["credit_balance"] == 0
    assert s["pending_eligibility_count"] == 0
