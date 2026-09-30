from datetime import datetime

from pydantic import BaseModel

from app.db.models import UnlockResult


class UnlockEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_id: int
    student_id: int | None
    member_id_raw: str
    result: UnlockResult
    created_at: datetime


class UnlockEventListResponse(BaseModel):
    items: list[UnlockEventResponse]
    next_cursor: int | None


class LedgerEntry(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    delta: int
    reason: str
    challenge_id: int | None
    redemption_id: int | None
    created_at: datetime


class LedgerResponse(BaseModel):
    student_id: int
    balance: int
    entries: list[LedgerEntry]
