from fastapi import APIRouter, status
from sqlalchemy import select

from app.core.dependencies import AdminDep, DbDep
from app.db.models import Item
from app.schemas.item import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemResponse])
async def list_items(db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Item).order_by(Item.id))
    return [ItemResponse.model_validate(r) for r in result.scalars().all()]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(body: ItemCreate, db: DbDep, _admin: AdminDep):
    item = Item(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ItemResponse.model_validate(item)
