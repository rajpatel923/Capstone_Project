import pytest

from app.core.security import encrypt_totp_secret, generate_totp_secret
from app.db.models import CreditLedger, Item, Student


async def _setup_student_with_credits(db_session, member_id: str, credits: int) -> Student:
    student = Student(
        member_id=member_id,
        full_name="Redeem Student",
        email=f"{member_id}@redeem.com",
        totp_secret_encrypted=encrypt_totp_secret(generate_totp_secret()),
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    if credits:
        ledger = CreditLedger(student_id=student.id, delta=credits, reason="test_grant")
        db_session.add(ledger)
        await db_session.commit()
    return student


async def _make_item(db_session, name: str, cost: int, stock: int) -> Item:
    item = Item(name=name, cost_credits=cost, stock_qty=stock)
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_redemption_success(client, db_session, fake_admin):
    student = await _setup_student_with_credits(db_session, "8001", 20)
    item = await _make_item(db_session, "Soda", 10, 5)

    resp = await client.post(
        "/redemptions",
        json={"student_id": student.id, "item_id": item.id},
    )
    assert resp.status_code == 201
    assert resp.json()["credits_spent"] == 10


@pytest.mark.asyncio
async def test_redemption_out_of_stock(client, db_session, fake_admin):
    student = await _setup_student_with_credits(db_session, "8002", 20)
    item = await _make_item(db_session, "Rare Item", 10, 0)

    resp = await client.post(
        "/redemptions",
        json={"student_id": student.id, "item_id": item.id},
    )
    assert resp.status_code == 409
    assert "out of stock" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_redemption_insufficient_credits(client, db_session, fake_admin):
    student = await _setup_student_with_credits(db_session, "8003", 3)
    item = await _make_item(db_session, "Expensive Item", 10, 5)

    resp = await client.post(
        "/redemptions",
        json={"student_id": student.id, "item_id": item.id},
    )
    assert resp.status_code == 409
    assert "insufficient" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_redemption_inactive_student(client, db_session, fake_admin):
    student = Student(
        member_id="8004",
        full_name="Inactive",
        email="inactive@redeem.com",
        totp_secret_encrypted=encrypt_totp_secret(generate_totp_secret()),
        active=False,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    item = await _make_item(db_session, "Active-Only Item", 1, 5)

    resp = await client.post(
        "/redemptions",
        json={"student_id": student.id, "item_id": item.id},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_redemption_item_not_found(client, db_session, fake_admin):
    student = await _setup_student_with_credits(db_session, "8005", 20)

    resp = await client.post(
        "/redemptions",
        json={"student_id": student.id, "item_id": 99999},
    )
    assert resp.status_code == 404
