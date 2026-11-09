
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Thread


async def create_category(
    user_id: UUID,
    name: str,
    slug: str,
    description: str,
    color: Optional[str],
    session: AsyncSession
) -> Category:

    if not (1 <= len(name) <= 50):
        raise ValueError("Name must be 1-50 characters")

    if not (10 <= len(description) <= 500):
        raise ValueError("Description must be 10-500 characters")

    if not re.match(r"^[a-z0-9_-]+$", slug):
        raise ValueError(
            "Slug must be lowercase alphanumeric, hyphens, underscores only"
        )

    existing = await session.execute(
        select(Category).where(
            and_(
                Category.user_id == user_id,
                Category.slug == slug
            )
        )
    )

    if existing.scalars().first():
        raise ValueError(f"Category with slug '{slug}' already exists")

    cat = Category(
        user_id=user_id,
        name=name,
        slug=slug,
        description=description,
        color=color or "#3B82F6"
    )

    session.add(cat)
    await session.commit()

    return cat


async def list_categories(
    user_id: UUID,
    session: AsyncSession
) -> List[Category]:

    result = await session.execute(
        select(Category)
        .where(Category.user_id == user_id)
        .where(Category.archived_at.is_(None))
        .order_by(Category.sort_order)
    )

    return result.scalars().all()


async def update_category(
    category_id: UUID,
    user_id: UUID,
    name: Optional[str],
    description: Optional[str],
    color: Optional[str],
    session: AsyncSession
) -> Category:
    """Update a category."""

    result = await session.execute(
        select(Category).where(
            and_(
                Category.id == category_id,
                Category.user_id == user_id
            )
        )
    )

    cat = result.scalars().first()

    if not cat:
        raise ValueError("Category not found")

    if name:
        if not (1 <= len(name) <= 50):
            raise ValueError("Name must be 1-50 characters")

        cat.name = name

    if description:
        if not (10 <= len(description) <= 500):
            raise ValueError("Description must be 10-500 characters")

        cat.description = description

    if color:
        cat.color = color

    await session.commit()

    return cat


async def archive_category(
    category_id: UUID,
    user_id: UUID,
    session: AsyncSession
) -> Category:

    result = await session.execute(
        select(Category).where(
            and_(
                Category.id == category_id,
                Category.user_id == user_id
            )
        )
    )

    cat = result.scalars().first()

    if not cat:
        raise ValueError("Category not found")

    uncategorized = await session.execute(
        select(Category).where(
            and_(
                Category.user_id == user_id,
                Category.slug == "uncategorized"
            )
        )
    )

    uncategorized = uncategorized.scalars().first()

    if not uncategorized:
        raise ValueError("Uncategorized category not found")

    await session.execute(
        update(Thread)
        .where(Thread.category_id == category_id)
        .values(
            category_id=uncategorized.id,
            class_status="needs_review"
        )
    )

    cat.archived_at = datetime.now(timezone.utc)

    await session.commit()

    return cat
