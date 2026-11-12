import pytest

from app.core.security import encrypt_totp_secret, generate_totp_secret, hash_api_key
from app.db.models import CreditLedger, Device, Student, UnlockEvent, UnlockResult


async def _make_device(db_session, name: str) -> Device:
    d = Device(device_name=name, api_key_hash=hash_api_key("dashkey"))
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


async def _make_student(db_session, member_id: str) -> Student:
    s = Student(
        member_id=member_id,
        full_name="Dash Student",
        email=f"{member_id}@dash.com",
        totp_secret_encrypted=encrypt_totp_secret(generate_totp_secret()),
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


@pytest.mark.asyncio
async def test_list_unlock_events_empty(client, db_session, fake_admin):
    resp = await client.get("/dashboard/unlock-events")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_list_unlock_events_with_data(client, db_session, fake_admin):
    device = await _make_device(db_session, "dash-device-1")
    student = await _make_student(db_session, "9001")
    event = UnlockEvent(
        device_id=device.id,
        student_id=student.id,
        member_id_raw=student.member_id,
        result=UnlockResult.granted,
    )
    db_session.add(event)
    await db_session.commit()

    resp = await client.get("/dashboard/unlock-events")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    results = [i["result"] for i in items]
    assert "granted" in results


@pytest.mark.asyncio
async def test_list_unlock_events_filter_by_result(client, db_session, fake_admin):
    device = await _make_device(db_session, "dash-device-2")
    event = UnlockEvent(
        device_id=device.id,
        student_id=None,
        member_id_raw="XXXX",
        result=UnlockResult.invalid_format,
    )
    db_session.add(event)
    await db_session.commit()

    resp = await client.get("/dashboard/unlock-events?result=invalid_format")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["result"] == "invalid_format"


@pytest.mark.asyncio
async def test_student_ledger(client, db_session, fake_admin):
    student = await _make_student(db_session, "9002")
    ledger = CreditLedger(student_id=student.id, delta=15, reason="test")
    db_session.add(ledger)
    await db_session.commit()

    resp = await client.get(f"/students/{student.id}/ledger")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 15
    assert len(data["entries"]) == 1


@pytest.mark.asyncio
async def test_student_ledger_not_found(client, db_session, fake_admin):
    resp = await client.get("/students/99999/ledger")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_devices(client, db_session, fake_admin):
    await _make_device(db_session, "list-device-test")
    resp = await client.get("/devices")
    assert resp.status_code == 200
    names = [d["device_name"] for d in resp.json()]
    assert "list-device-test" in names
