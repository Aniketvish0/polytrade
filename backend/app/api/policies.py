import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.policy import Policy
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.policy import PolicyCreate, PolicyResponse, PolicyUpdate

router = APIRouter()


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Policy).where(Policy.user_id == user.id))
    return result.scalars().all()


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    body: PolicyCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    policy = Policy(user_id=user.id, **body.model_dump())
    db.add(policy)
    await db.flush()
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id, Policy.user_id == user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id, Policy.user_id == user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(policy, field, value)
    await db.flush()
    return policy


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id, Policy.user_id == user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)


@router.post("/{policy_id}/activate", response_model=PolicyResponse)
async def activate_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Policy).where(Policy.user_id == user.id).values(is_active=False)
    )
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id, Policy.user_id == user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.is_active = True
    await db.flush()
    return policy


@router.post("/{policy_id}/deactivate", response_model=PolicyResponse)
async def deactivate_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id, Policy.user_id == user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.is_active = False
    await db.flush()
    return policy
