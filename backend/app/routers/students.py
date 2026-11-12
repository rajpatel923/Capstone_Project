from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminDep, DbDep
from app.core.security import (
    encrypt_totp_secret,
    generate_totp_secret,
    get_provisioning_uri,
)
from app.db.models import CreditLedger, Student, UnlockEligibility
from app.schemas.student import (
    StudentCreate,
    StudentEnrollResponse,
    StudentListResponse,
    StudentResetTotpResponse,
    StudentResponse,
    StudentUpdate,
)

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
