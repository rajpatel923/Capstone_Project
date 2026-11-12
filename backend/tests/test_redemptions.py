"""Tests for POST /redemptions — member_id lookup and credit_balance_after."""
import uuid

import pytest

from app.core.dependencies import require_admin
from app.core.security import encrypt_totp_secret, generate_totp_secret, hash_api_key
from app.db.models import Challenge, CreditLedger, Device, Item, Student, UnlockEligibility
from app.main import app


@pytest.fixture(autouse=True)
def override_admin():
    async def _fake_admin():
        return "test-admin"

    app.dependency_overrides[require_admin] = _fake_admin
    yield
    app.dependency_overrides.pop(require_admin, None)


async def _make_redemption_data(db_session, member_id: str, credits: int, item_cost: int, item_stock: int):
    """Create device, student, challenge, eligibility, credit ledger entry and item."""
    suffix = uuid.uuid4().hex[:8]
    device = Device(device_name=f"fridge-{suffix}", api_key_hash=hash_api_key(f"key-{suffix}"))
    db_session.add(device)

    student = Student(
        member_id=member_id,
        full_name=f"Tester {suffix}",
        email=f"tester-{suffix}@example.com",
        totp_secret_encrypted=encrypt_totp_secret(generate_totp_secret()),
    )
    db_session.add(student)
    await db_session.flush()

    challenge = Challenge(
        range_challenge_id=f"chall-{suffix}",
        title="Test Challenge",
        points=100,
    )
    db_session.add(challenge)
    await db_session.flush()

    eligibility = UnlockEligibility(
        student_id=student.id,
        challenge_id=challenge.id,
    )
    db_session.add(eligibility)

    ledger = CreditLedger(
        student_id=student.id,
        delta=credits,
        reason="test_grant",
    )
    db_session.add(ledger)

    item = Item(name=f"Item-{suffix}", cost_credits=item_cost, stock_qty=item_stock)
    db_session.add(item)

    await db_session.commit()
    await db_session.refresh(student)
    await db_session.refresh(item)

    return {"student": student, "item": item, "device": device}


@pytest.mark.asyncio
async def test_redemption_success(client, db_session):
    data = await _make_redemption_data(db_session, member_id="5678", credits=20, item_cost=5, item_stock=10)
    item_id = data["item"].id

    resp = await client.post(
        "/redemptions",
        json={"member_id": "5678", "item_id": item_id},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["credit_balance_after"] == 15  # 20 - 5
    assert body["credits_spent"] == 5


@pytest.mark.asyncio
async def test_redemption_insufficient_credits(client, db_session):
    data = await _make_redemption_data(db_session, member_id="5679", credits=20, item_cost=5, item_stock=20)
    item_id = data["item"].id

    # Spend until we can't afford any more (20 credits / 5 per item = 4 redemptions)
    for i in range(4):
        r = await client.post(
            "/redemptions",
            json={"member_id": "5679", "item_id": item_id},
        )
        assert r.status_code == 201, f"Redemption {i+1} failed: {r.text}"

    # 5th should fail
    resp = await client.post(
        "/redemptions",
        json={"member_id": "5679", "item_id": item_id},
    )
    assert resp.status_code == 409
    assert "insufficient" in resp.json()["detail"].lower()
