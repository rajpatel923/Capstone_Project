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
