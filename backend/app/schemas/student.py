from datetime import datetime

from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr


class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    active: bool | None = None


class StudentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    member_id: str
    full_name: str
    email: str
    active: bool
    created_at: datetime


class StudentEnrollResponse(StudentResponse):
    provisioning_uri: str


class StudentResetTotpResponse(BaseModel):
    member_id: str
    provisioning_uri: str


class StudentListResponse(BaseModel):
    items: list[StudentResponse]
    next_cursor: int | None


class BulkEnrollRow(BaseModel):
    full_name: str
    email: EmailStr


class BulkEnrollRequest(BaseModel):
    students: list[BulkEnrollRow]


class BulkEnrollRowResult(BaseModel):
    full_name: str
    email: str
    status: str  # "enrolled" | "skipped" | "error"
    reason: str | None
    member_id: str | None
    email_sent: bool


class BulkEnrollResponse(BaseModel):
    enrolled_count: int
    skipped_count: int
    results: list[BulkEnrollRowResult]
    email_enabled: bool
