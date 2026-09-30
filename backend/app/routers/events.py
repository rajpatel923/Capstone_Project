from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import DbDep
from app.core.security import verify_hmac_signature
from app.db.models import Challenge, CreditLedger, Student, UnlockEligibility
from app.schemas.event import FlagCapturedPayload

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/flag-captured", status_code=status.HTTP_204_NO_CONTENT)
async def flag_captured(
    request: Request,
    db: DbDep,
    x_range_signature: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    body_bytes = await request.body()

    # Verify HMAC signature (ADR-004); fall back to bearer token
    if x_range_signature:
        if not verify_hmac_signature(body_bytes, x_range_signature, settings.range_webhook_secret):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    elif authorization:
        token = authorization.removeprefix("Bearer ").strip()
        if token != settings.range_webhook_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication")

    payload = FlagCapturedPayload.model_validate_json(body_bytes)

    # Upsert challenge
    challenge_result = await db.execute(
        select(Challenge).where(Challenge.range_challenge_id == payload.range_challenge_id)
    )
    challenge = challenge_result.scalar_one_or_none()
    if challenge is None:
        challenge = Challenge(
            range_challenge_id=payload.range_challenge_id,
            title=payload.title,
            points=payload.points,
        )
        db.add(challenge)
        await db.flush()
    else:
        challenge.points = payload.points
        challenge.title = payload.title

    # Find student
    student_result = await db.execute(
        select(Student).where(Student.member_id == payload.student_member_id)
    )
    student = student_result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    now = datetime.now(timezone.utc)

    # Grant unlock eligibility (1-hour window)
    eligibility = UnlockEligibility(
        student_id=student.id,
        challenge_id=challenge.id,
        granted_at=now,
        expires_at=now + timedelta(hours=1),
    )
    db.add(eligibility)

    # Credit ledger entry
    credits = payload.points // settings.credit_conversion_rate
    if credits > 0:
        ledger = CreditLedger(
            student_id=student.id,
            delta=credits,
            reason="flag_captured",
            challenge_id=challenge.id,
        )
        db.add(ledger)

    await db.commit()
