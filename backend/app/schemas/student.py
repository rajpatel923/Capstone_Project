from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class StudentCreate(BaseModel):
    member_id: str
    full_name: str
    email: EmailStr

    @field_validator("member_id")
    @classmethod
    def member_id_must_be_4_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 4:
            raise ValueError("member_id must be exactly 4 digits")
        return v


class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    active: bool | None = None


class StudentResponse(BaseModel):
    id: int
    member_id: str
    full_name: str
    email: str
    active: bool
    created_at: datetime
    credit_balance: int = 0
    pending_eligibility_count: int = 0


class StudentEnrollResponse(StudentResponse):
    totp_provisioning_uri: str


class StudentResetTotpResponse(BaseModel):
    member_id: str
    totp_provisioning_uri: str


class StudentListResponse(BaseModel):
    items: list[StudentResponse]
    next_cursor: int | None
