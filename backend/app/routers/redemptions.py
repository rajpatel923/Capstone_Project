from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.dependencies import AdminDep, DbDep
from app.db.models import CreditLedger, Item, Redemption, Student
from app.schemas.redemption import RedemptionCreate, RedemptionResponse

router = APIRouter(prefix="/redemptions", tags=["redemptions"])


@router.post("", response_model=RedemptionResponse, status_code=status.HTTP_201_CREATED)
async def create_redemption(body: RedemptionCreate, db: DbDep, _admin: AdminDep):
    student_result = await db.execute(select(Student).where(Student.id == body.student_id))
    student = student_result.scalar_one_or_none()
    if not student or not student.active:
        raise HTTPException(status_code=404, detail="Student not found or inactive")

    item_result = await db.execute(select(Item).where(Item.id == body.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.stock_qty < 1:
        raise HTTPException(status_code=409, detail="Item out of stock")

    # Calculate current balance
    balance_result = await db.execute(
        select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(
            CreditLedger.student_id == student.id
        )
    )
    balance = balance_result.scalar_one()

    if balance < item.cost_credits:
        raise HTTPException(status_code=409, detail="Insufficient credits")

    redemption = Redemption(
        student_id=student.id,
        item_id=item.id,
        credits_spent=item.cost_credits,
    )
    db.add(redemption)
    await db.flush()

    item.stock_qty -= 1
    ledger = CreditLedger(
        student_id=student.id,
        delta=-item.cost_credits,
        reason="redemption",
        redemption_id=redemption.id,
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(redemption)
    return RedemptionResponse.model_validate(redemption)
