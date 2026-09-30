from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.dependencies import AdminDep, DbDep
from app.db.models import CreditLedger, Device, Student, UnlockEvent, UnlockResult
from app.schemas.dashboard import (
    LedgerEntry,
    LedgerResponse,
    UnlockEventListResponse,
    UnlockEventResponse,
)
from app.schemas.device import DeviceResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/unlock-events", response_model=UnlockEventListResponse)
async def list_unlock_events(
    db: DbDep,
    _admin: AdminDep,
    student_id: int | None = Query(default=None),
    device_id: int | None = Query(default=None),
    result: UnlockResult | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    cursor: int | None = Query(default=None),
):
    q = select(UnlockEvent).order_by(UnlockEvent.id)
    if student_id:
        q = q.where(UnlockEvent.student_id == student_id)
    if device_id:
        q = q.where(UnlockEvent.device_id == device_id)
    if result:
        q = q.where(UnlockEvent.result == result)
    if cursor:
        q = q.where(UnlockEvent.id > cursor)
    q = q.limit(limit + 1)
    rows = (await db.execute(q)).scalars().all()
    next_cursor = rows[-1].id if len(rows) > limit else None
    return UnlockEventListResponse(
        items=[UnlockEventResponse.model_validate(r) for r in rows[:limit]],
        next_cursor=next_cursor,
    )


@router.get("/students/{student_id}/ledger", response_model=LedgerResponse)
async def student_ledger(student_id: int, db: DbDep, _admin: AdminDep):
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    if not student_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")

    entries_result = await db.execute(
        select(CreditLedger)
        .where(CreditLedger.student_id == student_id)
        .order_by(CreditLedger.created_at)
    )
    entries = entries_result.scalars().all()
    balance = sum(e.delta for e in entries)
    return LedgerResponse(
        student_id=student_id,
        balance=balance,
        entries=[LedgerEntry.model_validate(e) for e in entries],
    )


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices(db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Device).order_by(Device.id))
    devices = result.scalars().all()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=60)
    return [
        DeviceResponse(
            id=d.id,
            device_name=d.device_name,
            firmware_version=d.firmware_version,
            last_seen_at=d.last_seen_at,
            online=d.last_seen_at is not None and d.last_seen_at > cutoff,
        )
        for d in devices
    ]
