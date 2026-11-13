from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import AdminDep, DbDep
from app.core.security import (
    encrypt_totp_secret,
    generate_totp_secret,
    get_provisioning_uri,
)
from app.db.models import CreditLedger, Student, UnlockEligibility
from app.schemas.student import (
    BulkEnrollRequest,
    BulkEnrollResponse,
    BulkEnrollRowResult,
    StudentCreate,
    StudentEnrollResponse,
    StudentListResponse,
    StudentResetTotpResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services.email import send_enrollment_email

router = APIRouter(prefix="/students", tags=["students"])


async def _enrich_student(student: Student, db: AsyncSession) -> StudentResponse:
    balance_result = await db.execute(
        select(func.coalesce(func.sum(CreditLedger.delta), 0))
        .where(CreditLedger.student_id == student.id)
    )
    balance = balance_result.scalar_one()

    now = datetime.now(timezone.utc)
    elig_result = await db.execute(
        select(func.count(UnlockEligibility.id))
        .where(
            UnlockEligibility.student_id == student.id,
            UnlockEligibility.consumed_at.is_(None),
            UnlockEligibility.expires_at > now,
        )
    )
    pending = elig_result.scalar_one()

    return StudentResponse(
        id=student.id,
        member_id=student.member_id,
        full_name=student.full_name,
        email=student.email,
        active=student.active,
        created_at=student.created_at,
        credit_balance=balance,
        pending_eligibility_count=pending,
    )


@router.post("", response_model=StudentEnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(body: StudentCreate, db: DbDep, _admin: AdminDep):
    # Check for duplicate member_id
    existing_mid = await db.execute(select(Student).where(Student.member_id == body.member_id))
    if existing_mid.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="member_id already in use")

    # Check for duplicate email
    existing = await db.execute(select(Student).where(Student.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already enrolled")

    secret = generate_totp_secret()
    encrypted = encrypt_totp_secret(secret)
    provisioning_uri = get_provisioning_uri(secret, body.member_id)

    student = Student(
        member_id=body.member_id,
        full_name=body.full_name,
        email=body.email,
        totp_secret_encrypted=encrypted,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)

    base = await _enrich_student(student, db)
    return StudentEnrollResponse(**base.model_dump(), totp_provisioning_uri=provisioning_uri)


@router.post("/bulk", response_model=BulkEnrollResponse, status_code=status.HTTP_200_OK)
async def bulk_enroll_students(body: BulkEnrollRequest, db: DbDep, _admin: AdminDep):
    """
    Enroll multiple students in one request. Skips duplicate emails gracefully.
    Sends a TOTP setup email to each enrolled student if SMTP is configured.
    """
    results: list[BulkEnrollRowResult] = []

    for row in body.students:
        existing = await db.execute(select(Student).where(Student.email == row.email))
        if existing.scalar_one_or_none() is not None:
            results.append(BulkEnrollRowResult(
                full_name=row.full_name,
                email=row.email,
                status="skipped",
                reason="Email already enrolled",
                member_id=None,
                email_sent=False,
            ))
            continue

        try:
            member_id = await _generate_unique_member_id(db)
            secret = generate_totp_secret()
            encrypted = encrypt_totp_secret(secret)
            provisioning_uri = get_provisioning_uri(secret, member_id)
            student = Student(
                member_id=member_id,
                full_name=row.full_name,
                email=row.email,
                totp_secret_encrypted=encrypted,
            )
            db.add(student)
            await db.commit()
            await db.refresh(student)
        except Exception as exc:
            await db.rollback()
            results.append(BulkEnrollRowResult(
                full_name=row.full_name,
                email=row.email,
                status="error",
                reason=str(exc),
                member_id=None,
                email_sent=False,
            ))
            continue

        email_sent = False
        try:
            email_sent = await send_enrollment_email(
                to_email=row.email,
                full_name=row.full_name,
                member_id=member_id,
                provisioning_uri=provisioning_uri,
            )
        except Exception:
            pass

        results.append(BulkEnrollRowResult(
            full_name=row.full_name,
            email=row.email,
            status="enrolled",
            reason=None,
            member_id=member_id,
            email_sent=email_sent,
        ))

    enrolled_count = sum(1 for r in results if r.status == "enrolled")
    skipped_count = len(results) - enrolled_count
    return BulkEnrollResponse(
        enrolled_count=enrolled_count,
        skipped_count=skipped_count,
        results=results,
        email_enabled=bool(settings.smtp_host),
    )


@router.get("", response_model=StudentListResponse)
async def list_students(
    db: DbDep,
    _admin: AdminDep,
    limit: int = Query(default=50, le=200),
    cursor: int | None = Query(default=None),
):
    q = select(Student).order_by(Student.id)
    if cursor:
        q = q.where(Student.id > cursor)
    q = q.limit(limit + 1)
    result = await db.execute(q)
    rows = result.scalars().all()
    next_cursor = rows[-1].id if len(rows) > limit else None
    items = [await _enrich_student(r, db) for r in rows[:limit]]
    return StudentListResponse(
        items=items,
        next_cursor=next_cursor,
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return await _enrich_student(student, db)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: int, body: StudentUpdate, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, value)

    if body.active is False:
        await db.execute(
            sa_update(UnlockEligibility)
            .where(
                UnlockEligibility.student_id == student_id,
                UnlockEligibility.consumed_at.is_(None),
            )
            .values(consumed_at=datetime.now(timezone.utc))
        )

    await db.commit()
    await db.refresh(student)
    return await _enrich_student(student, db)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: int, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await db.delete(student)
    await db.commit()


@router.post("/{student_id}/reset-totp", response_model=StudentResetTotpResponse)
async def reset_totp(student_id: int, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    secret = generate_totp_secret()
    student.totp_secret_encrypted = encrypt_totp_secret(secret)
    await db.commit()
    return StudentResetTotpResponse(
        member_id=student.member_id,
        totp_provisioning_uri=get_provisioning_uri(secret, student.member_id),
    )
