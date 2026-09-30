from datetime import datetime

from pydantic import BaseModel


class RedemptionCreate(BaseModel):
    student_id: int
    item_id: int


class RedemptionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    student_id: int
    item_id: int
    credits_spent: int
    created_at: datetime
