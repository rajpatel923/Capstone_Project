import pytest

from app.core.security import (
    encrypt_totp_secret,
    generate_totp_secret,
    hash_api_key,
    verify_totp,
)
from app.db.models import Device, Student


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
    import pyotp
    code = pyotp.TOTP(secret).now()
    assert verify_totp(encrypted, code) is True
    assert verify_totp(encrypted, "000000") is False
