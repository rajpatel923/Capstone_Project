import hashlib
import hmac
import json

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import encrypt_totp_secret, generate_totp_secret
from app.db.models import CreditLedger, Student


def _make_sig(body: bytes) -> str:
    sig = hmac.new(settings.range_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


async def _enroll(db_session, member_id: str) -> Student:
    student = Student(
        member_id=member_id,
        full_name="Webhook Student",
        email=f"{member_id}@webhook.com",
        totp_secret_encrypted=encrypt_totp_secret(generate_totp_secret()),
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


@pytest.mark.asyncio
async def test_flag_captured_hmac_auth(client, db_session):
    student = await _enroll(db_session, "5555")
    payload = json.dumps({
        "range_challenge_id": "ch-hmac-1",
        "title": "HMAC Challenge",
        "points": 100,
        "student_member_id": student.member_id,
    }).encode()

    resp = await client.post(
        "/events/flag-captured",
        content=payload,
        headers={
            "content-type": "application/json",
            "x-range-signature": _make_sig(payload),
        },
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_flag_captured_bearer_auth(client, db_session):
    student = await _enroll(db_session, "6666")
    payload = json.dumps({
        "range_challenge_id": "ch-bearer-1",
        "title": "Bearer Challenge",
        "points": 50,
        "student_member_id": student.member_id,
    }).encode()

    resp = await client.post(
        "/events/flag-captured",
        content=payload,
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {settings.range_webhook_secret}",
        },
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_flag_captured_bad_signature(client, db_session):
    payload = json.dumps({
        "range_challenge_id": "ch-bad",
        "title": "Bad",
        "points": 10,
        "student_member_id": "0000",
    }).encode()

    resp = await client.post(
        "/events/flag-captured",
        content=payload,
        headers={
            "content-type": "application/json",
            "x-range-signature": "sha256=deadbeef",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_flag_captured_no_auth(client, db_session):
    payload = json.dumps({
        "range_challenge_id": "ch-no-auth",
        "title": "No Auth",
        "points": 10,
        "student_member_id": "0000",
    }).encode()

    resp = await client.post(
        "/events/flag-captured",
        content=payload,
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_flag_captured_creates_credit_entry(client, db_session):
    student = await _enroll(db_session, "7777")
    payload = json.dumps({
        "range_challenge_id": "ch-credit-1",
        "title": "Credit Challenge",
        "points": 100,
        "student_member_id": student.member_id,
    }).encode()

    await client.post(
        "/events/flag-captured",
        content=payload,
        headers={
            "content-type": "application/json",
            "x-range-signature": _make_sig(payload),
        },
    )

    # credit_conversion_rate defaults to 10, so 100 points = 10 credits
    result = await db_session.execute(
        select(func.sum(CreditLedger.delta)).where(CreditLedger.student_id == student.id)
    )
    assert result.scalar_one() == 10


@pytest.mark.asyncio
async def test_flag_captured_student_not_found(client, db_session):
    payload = json.dumps({
        "range_challenge_id": "ch-notfound",
        "title": "Missing Student",
        "points": 10,
        "student_member_id": "9999",
    }).encode()

    resp = await client.post(
        "/events/flag-captured",
        content=payload,
        headers={
            "content-type": "application/json",
            "x-range-signature": _make_sig(payload),
        },
    )
    assert resp.status_code == 404
