from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    cost_credits: int
    stock_qty: int = 0


class ItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    cost_credits: int
    stock_qty: int
