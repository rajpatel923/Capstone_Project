from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_clerk_payload, hash_api_key, get_clerk_user_role
from app.db.models import Device
from app.db.session import get_db


async def require_admin(request: Request) -> str:
    """Verify Clerk session JWT and require role=admin in publicMetadata."""
    try:
        payload = get_clerk_payload(request)
        user_id = payload["sub"]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    role = get_clerk_user_role(user_id)
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return user_id


async def require_device(
    device_id: int,
    x_device_key: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Device:
    """Verify device API key; return the Device row."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None or device.api_key_hash != hash_api_key(x_device_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device key")
    return device


DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[str, Depends(require_admin)]
