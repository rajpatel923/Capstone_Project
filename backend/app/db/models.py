import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _one_hour_from_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[str] = mapped_column(String(4), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    totp_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    eligibilities: Mapped[list["UnlockEligibility"]] = relationship(back_populates="student")
    unlock_events: Mapped[list["UnlockEvent"]] = relationship(back_populates="student")
    credit_entries: Mapped[list["CreditLedger"]] = relationship(back_populates="student")
    redemptions: Mapped[list["Redemption"]] = relationship(back_populates="student")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    range_challenge_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    eligibilities: Mapped[list["UnlockEligibility"]] = relationship(back_populates="challenge")
    credit_entries: Mapped[list["CreditLedger"]] = relationship(back_populates="challenge")


class UnlockEligibility(Base):
    __tablename__ = "unlock_eligibilities"
    __table_args__ = (Index("ix_eligibility_student_consumed", "student_id", "consumed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_one_hour_from_now, nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship(back_populates="eligibilities")
    challenge: Mapped["Challenge"] = relationship(back_populates="eligibilities")


class UnlockResult(str, enum.Enum):
    granted = "granted"
    invalid_format = "invalid_format"
    unknown_member = "unknown_member"
    invalid_totp = "invalid_totp"
    no_eligibility = "no_eligibility"
    member_inactive = "member_inactive"
    forced_open = "forced_open"


class UnlockEvent(Base):
    __tablename__ = "unlock_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True)
    member_id_raw: Mapped[str] = mapped_column(String(10), nullable=False)
    result: Mapped[UnlockResult] = mapped_column(Enum(UnlockResult), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    device: Mapped["Device"] = relationship(back_populates="unlock_events")
    student: Mapped["Student | None"] = relationship(back_populates="unlock_events")


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    challenge_id: Mapped[int | None] = mapped_column(ForeignKey("challenges.id"), nullable=True)
    redemption_id: Mapped[int | None] = mapped_column(
        ForeignKey("redemptions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="credit_entries")
    challenge: Mapped["Challenge | None"] = relationship(back_populates="credit_entries")
    redemption: Mapped["Redemption | None"] = relationship(back_populates="credit_entries")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    unlock_events: Mapped[list["UnlockEvent"]] = relationship(back_populates="device")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cost_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    redemptions: Mapped[list["Redemption"]] = relationship(back_populates="item")


class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    credits_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="redemptions")
    item: Mapped["Item"] = relationship(back_populates="redemptions")
    credit_entries: Mapped[list["CreditLedger"]] = relationship(back_populates="redemption")
