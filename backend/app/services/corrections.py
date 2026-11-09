import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Correction, Thread


logger = logging.getLogger(__name__)


async def record_correction(
    user_id: UUID,
    thread_id: UUID,
    corrected_category_id: UUID,
    reason: Optional[str],
    session: AsyncSession
) -> Correction:
    """Record a user correction and update thread category."""

    thread_result = await session.execute(
        select(Thread)
        .join(Category, Category.user_id == user_id)
        .where(Thread.id == thread_id)
    )
    thread = thread_result.scalars().first()

    if not thread:
        raise ValueError("Thread not found")

    category_result = await session.execute(
        select(Category).where(
            and_(
                Category.id == corrected_category_id,
                Category.user_id == user_id
            )
        )
    )
    category = category_result.scalars().first()

    if not category:
        raise ValueError("Category not found")

    correction = Correction(
        user_id=user_id,
        thread_id=thread_id,
        predicted_category_id=thread.category_id,
        corrected_category_id=corrected_category_id,
        reason=reason
    )
    session.add(correction)

    thread.category_id = corrected_category_id
    thread.class_status = "corrected"
    thread.classified_at = datetime.now(timezone.utc)

    await session.commit()

    return correction


async def list_corrections(
    user_id: UUID,
    session: AsyncSession
) -> list:
    """List the user's corrections."""

    result = await session.execute(
        select(Correction)
        .where(Correction.user_id == user_id)
        .order_by(Correction.created_at.desc())
        .limit(100)
    )

    return result.scalars().all()