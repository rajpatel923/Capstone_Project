from datetime import datetime, timedelta, timezone

import pyotp
import pytest

from app.core.security import encrypt_totp_secret, generate_totp_secret, hash_api_key, verify_totp
from app.db.models import Challenge, Device, Student, UnlockEligibility


async def _make_device(db_session, name: str, key: str) -> Device:
    device = Device(device_name=name, api_key_hash=hash_api_key(key))
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


async def _make_student(db_session, member_id: str, active: bool = True) -> tuple[Student, str]:
    secret = generate_totp_secret()
    student = Student(
        member_id=member_id,
        full_name="Test Student",
        email=f"{member_id}@test.com",
        totp_secret_encrypted=encrypt_totp_secret(secret),
        active=active,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student, secret


@pytest.mark.asyncio
async def test_validate_code_invalid_format(client, db_session):
    device = Device(device_name="esp32-test", api_key_hash=hash_api_key("testkey"))
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": "123"},
        headers={"x-device-key": "testkey"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["reason"] == "invalid_format"


@pytest.mark.asyncio
async def test_validate_code_unknown_member(client, db_session):
    device = Device(device_name="esp32-test2", api_key_hash=hash_api_key("testkey2"))
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": "9999123456"},
        headers={"x-device-key": "testkey2"},
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "unknown_member"


@pytest.mark.asyncio
async def test_verify_totp_roundtrip():
    secret = generate_totp_secret()
    encrypted = encrypt_totp_secret(secret)
    code = pyotp.TOTP(secret, interval=60).now()
    assert verify_totp(encrypted, code) is True
    assert verify_totp(encrypted, "000000") is False


@pytest.mark.asyncio
async def test_validate_code_member_inactive(client, db_session):
    device = await _make_device(db_session, "esp32-inactive", "key-inactive")
    student, secret = await _make_student(db_session, "1111", active=False)
    code = student.member_id + pyotp.TOTP(secret, interval=60).now()

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": code},
        headers={"x-device-key": "key-inactive"},
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "member_inactive"


@pytest.mark.asyncio
async def test_validate_code_invalid_totp(client, db_session):
    device = await _make_device(db_session, "esp32-badtotp", "key-badtotp")
    student, _ = await _make_student(db_session, "2222")
    code = student.member_id + "000000"

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": code},
        headers={"x-device-key": "key-badtotp"},
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "invalid_totp"


@pytest.mark.asyncio
async def test_validate_code_no_eligibility(client, db_session):
    device = await _make_device(db_session, "esp32-noelig", "key-noelig")
    student, secret = await _make_student(db_session, "3333")
    code = student.member_id + pyotp.TOTP(secret, interval=60).now()

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": code},
        headers={"x-device-key": "key-noelig"},
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "no_eligibility"


@pytest.mark.asyncio
async def test_validate_code_granted(client, db_session):
    device = await _make_device(db_session, "esp32-granted", "key-granted")
    student, secret = await _make_student(db_session, "4444")

    challenge = Challenge(range_challenge_id="ch-1", title="Test", points=100)
    db_session.add(challenge)
    await db_session.commit()
    await db_session.refresh(challenge)

    now = datetime.now(timezone.utc)
    eligibility = UnlockEligibility(
        student_id=student.id,
        challenge_id=challenge.id,
        granted_at=now,
        expires_at=now + timedelta(hours=1),
    )
    db_session.add(eligibility)
    await db_session.commit()

    code = student.member_id + pyotp.TOTP(secret, interval=60).now()
    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": code},
        headers={"x-device-key": "key-granted"},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True
    assert resp.json()["reason"] == "granted"


@pytest.mark.asyncio
async def test_validate_code_bad_device_key(client, db_session):
    device = await _make_device(db_session, "esp32-badkey", "correct-key")

    resp = await client.post(
        f"/devices/{device.id}/validate-code",
        json={"code": "1234123456"},
        headers={"x-device-key": "wrong-key"},
    )
    assert resp.status_code == 401
