import random
import string

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminDep, DbDep
from app.core.security import (
    encrypt_totp_secret,
    generate_totp_secret,
    get_provisioning_uri,
)
from app.db.models import Student
from app.schemas.student import (
    StudentCreate,
    StudentEnrollResponse,
    StudentListResponse,
    StudentResetTotpResponse,
    StudentResponse,
    StudentUpdate,
)

router = APIRouter(prefix="/students", tags=["students"])


async def _generate_unique_member_id(db: AsyncSession) -> str:
    for _ in range(20):
        candidate = "".join(random.choices(string.digits, k=4))
        existing = await db.execute(select(Student).where(Student.member_id == candidate))
        if existing.scalar_one_or_none() is None:
            return candidate
    raise RuntimeError("Could not generate unique member_id after 20 attempts")


@router.post("", response_model=StudentEnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(body: StudentCreate, db: DbDep, _admin: AdminDep):
    existing = await db.execute(select(Student).where(Student.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already enrolled")

    member_id = await _generate_unique_member_id(db)
    secret = generate_totp_secret()
    encrypted = encrypt_totp_secret(secret)
    provisioning_uri = get_provisioning_uri(secret, member_id)

    student = Student(
        member_id=member_id,
        full_name=body.full_name,
        email=body.email,
        totp_secret_encrypted=encrypted,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return StudentEnrollResponse(**StudentResponse.model_validate(student).model_dump(), provisioning_uri=provisioning_uri)


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
    return StudentListResponse(
        items=[StudentResponse.model_validate(r) for r in rows[:limit]],
        next_cursor=next_cursor,
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse.model_validate(student)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: int, body: StudentUpdate, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


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
        provisioning_uri=get_provisioning_uri(secret, student.member_id),
    )
