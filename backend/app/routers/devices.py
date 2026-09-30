from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import DbDep
from app.core.rate_limit import limiter
from app.core.security import hash_api_key, verify_totp
from app.db.models import Device, Student, UnlockEligibility, UnlockEvent, UnlockResult
from app.schemas.device import (
    DeviceEventRequest,
    DeviceStateResponse,
    ValidateCodeRequest,
    ValidateCodeResponse,
)

router = APIRouter(prefix="/devices", tags=["devices"])


async def _get_device(device_id: int, x_device_key: str, db: AsyncSession) -> Device:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None or device.api_key_hash != hash_api_key(x_device_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device key")
    return device


async def _log_event(
    db: AsyncSession,
    device: Device,
    member_id_raw: str,
    result: UnlockResult,
    student_id: int | None,
) -> None:
    event = UnlockEvent(
        device_id=device.id,
        student_id=student_id,
        member_id_raw=member_id_raw,
        result=result,
    )
    db.add(event)
    await db.commit()


@router.post("/{device_id}/validate-code", response_model=ValidateCodeResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def validate_code(device_id: int, body: ValidateCodeRequest, request: Request, db: DbDep):
    x_device_key = request.headers.get("x-device-key", "")
    device = await _get_device(device_id, x_device_key, db)

    code = body.code.strip()
    if len(code) != 10 or not code.isdigit():
        await _log_event(db, device, code[:10], UnlockResult.invalid_format, None)
        return ValidateCodeResponse(valid=False, reason="invalid_format")

    member_id_raw = code[:4]
    totp_code = code[4:]

    student_result = await db.execute(select(Student).where(Student.member_id == member_id_raw))
    student = student_result.scalar_one_or_none()

    if student is None:
        await _log_event(db, device, member_id_raw, UnlockResult.unknown_member, None)
        return ValidateCodeResponse(valid=False, reason="unknown_member")

    if not student.active:
        await _log_event(db, device, member_id_raw, UnlockResult.member_inactive, student.id)
        return ValidateCodeResponse(valid=False, reason="member_inactive")

    if not verify_totp(student.totp_secret_encrypted, totp_code):
        await _log_event(db, device, member_id_raw, UnlockResult.invalid_totp, student.id)
        return ValidateCodeResponse(valid=False, reason="invalid_totp")

    now = datetime.now(timezone.utc)
    eligibility_result = await db.execute(
        select(UnlockEligibility)
        .where(
            UnlockEligibility.student_id == student.id,
            UnlockEligibility.consumed_at.is_(None),
            UnlockEligibility.expires_at > now,
        )
        .order_by(UnlockEligibility.granted_at)
        .limit(1)
    )
    eligibility = eligibility_result.scalar_one_or_none()

    if eligibility is None:
        await _log_event(db, device, member_id_raw, UnlockResult.no_eligibility, student.id)
        return ValidateCodeResponse(valid=False, reason="no_eligibility")

    eligibility.consumed_at = now
    await _log_event(db, device, member_id_raw, UnlockResult.granted, student.id)
    return ValidateCodeResponse(valid=True, reason="granted")


@router.post("/{device_id}/events", status_code=status.HTTP_204_NO_CONTENT)
async def device_event(device_id: int, body: DeviceEventRequest, request: Request, db: DbDep):
    x_device_key = request.headers.get("x-device-key", "")
    device = await _get_device(device_id, x_device_key, db)

    device.last_seen_at = datetime.now(timezone.utc)
    if body.firmware_version:
        device.firmware_version = body.firmware_version

    if body.event_type == "forced_open":
        event = UnlockEvent(
            device_id=device.id,
            student_id=None,
            member_id_raw="",
            result=UnlockResult.forced_open,
        )
        db.add(event)

    await db.commit()


@router.get("/{device_id}/state", response_model=DeviceStateResponse)
async def device_state(device_id: int, request: Request, db: DbDep):
    x_device_key = request.headers.get("x-device-key", "")
    await _get_device(device_id, x_device_key, db)
    return DeviceStateResponse()
