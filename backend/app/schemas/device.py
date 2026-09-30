from datetime import datetime

from pydantic import BaseModel


class ValidateCodeRequest(BaseModel):
    code: str


class ValidateCodeResponse(BaseModel):
    valid: bool
    reason: str


class DeviceEventRequest(BaseModel):
    event_type: str  # "forced_open" | "heartbeat"
    firmware_version: str | None = None


class DeviceStateResponse(BaseModel):
    pending_command: None = None  # always null in v1


class DeviceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_name: str
    firmware_version: str | None
    last_seen_at: datetime | None
    online: bool
