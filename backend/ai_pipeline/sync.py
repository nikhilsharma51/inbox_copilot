
import os
import logging
import hashlib

from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import update, select

from ai_pipeline.mcp_client.client import get_tools
from app.db.models import Mailbox, Thread
from app.db.session import AsyncSession


logger = logging.getLogger(__name__)


async def get_valid_access_token(
    mailbox: Mailbox,
    session: AsyncSession
) -> str:
    token = os.getenv("GMAIL_ACCESS_TOKEN")

    if not token:
        raise ValueError("GMAIL_ACCESS_TOKEN not set")

    return token


def parse_datetime(value) -> datetime | None:

    if not value:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    return None


async def sync_mailbox(
    mailbox_id: UUID,
    session: AsyncSession
) -> dict:
    stale_lock_minutes = 10
    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(minutes=stale_lock_minutes)

    mailbox_result = await session.execute(
        select(Mailbox).where(Mailbox.id == mailbox_id)
    )
    mailbox = mailbox_result.scalar_one_or_none()

    if not mailbox:
        raise ValueError(f"Mailbox {mailbox_id} not found")

    try:
        # Atomically claim the mailbox for synchronization.
        stmt = (
            update(Mailbox)
            .where(
                Mailbox.id == mailbox_id,
                (
                    (Mailbox.sync_status != "syncing")
                    | (Mailbox.sync_started_at.is_(None))
                    | (Mailbox.sync_started_at < stale_before)
                )
            )
            .values(
                sync_status="syncing",
                sync_started_at=now
            )
            .returning(Mailbox.id)
        )

        result = await session.execute(stmt)
        claimed_mailbox = result.scalar_one_or_none()

        if claimed_mailbox is None:
            await session.rollback()
            logger.info("Mailbox %s is already syncing", mailbox_id)
            return {"status": "already_syncing"}

        # Release the database transaction while Gmail is being queried.
        await session.commit()

        try:
            access_token = await get_valid_access_token(mailbox, session)

        except ValueError:
            logger.exception("Authentication failed for mailbox %s", mailbox_id)

            await session.rollback()
            await session.execute(
                update(Mailbox)
                .where(Mailbox.id == mailbox_id)
                .values(
                    sync_status="idle",
                    sync_started_at=None,
                    status="needs_reconnect"
                )
            )
            await session.commit()
            raise

        query = f"newer_than:{mailbox.backfill_days}d"
        max_results = 20

        mcp_tools = await get_tools("reader", access_token, "fake")
        threads_data = await mcp_tools.list_threads(query, max_results)

        threads_list = (
            threads_data.get("threads", [])
            if isinstance(threads_data, dict)
            else []
        )

        gmail_thread_ids = [
            item["id"]
            for item in threads_list
            if isinstance(item, dict) and item.get("id")
        ]

        existing_threads = {}

        if gmail_thread_ids:
            result = await session.execute(
                select(Thread).where(
                    Thread.mailbox_id == mailbox_id,
                    Thread.gmail_thread_id.in_(gmail_thread_ids)
                )
            )

            existing_threads = {
                thread.gmail_thread_id: thread
                for thread in result.scalars().all()
            }

        synced_count = 0

        for thread_data in threads_list:
            if not isinstance(thread_data, dict) or not thread_data.get("id"):
                continue

            gmail_thread_id = thread_data["id"]

            content_hash_input = (
                f"{thread_data.get('last_message_id', '')}"
                f"{thread_data.get('message_count', 0)}"
            )

            content_hash = hashlib.sha256(
                content_hash_input.encode()
            ).hexdigest()

            participants = thread_data.get("participants", [])

            if not isinstance(participants, list):
                participants = []

            last_message_at = parse_datetime(
                thread_data.get("last_message_at")
            )

            thread = existing_threads.get(gmail_thread_id)

            if thread:
                # Update the existing thread with the latest Gmail data.
                thread.subject = thread_data.get("subject")
                thread.snippet = thread_data.get("snippet")
                thread.participants = participants
                thread.last_message_at = last_message_at
                thread.message_count = thread_data.get("message_count", 0)

                if content_hash != thread.content_hash:
                    thread.classified_at = None
                    thread.class_status = "unreviewed"

                thread.content_hash = content_hash
                thread.updated_at = datetime.now(timezone.utc)

            else:
                # Create a new thread when it hasn't been synced before.
                thread = Thread(
                    mailbox_id=mailbox_id,
                    gmail_thread_id=gmail_thread_id,
                    subject=thread_data.get("subject"),
                    snippet=thread_data.get("snippet"),
                    participants=participants,
                    last_message_at=last_message_at,
                    message_count=thread_data.get("message_count", 0),
                    content_hash=content_hash,
                    class_status="unreviewed"
                )

                session.add(thread)
                existing_threads[gmail_thread_id] = thread

            synced_count += 1

        await session.commit()

        await session.execute(
            update(Mailbox)
            .where(Mailbox.id == mailbox_id)
            .values(
                sync_status="idle",
                sync_started_at=None,
                last_sync_at=datetime.now(timezone.utc)
            )
        )
        await session.commit()

        logger.info(
            "Synced %s threads for mailbox %s",
            synced_count,
            mailbox_id
        )

        return {"synced": synced_count}

    except Exception:
        logger.exception("Sync failed for mailbox %s", mailbox_id)

        try:
            await session.rollback()

            await session.execute(
                update(Mailbox)
                .where(Mailbox.id == mailbox_id)
                .values(
                    sync_status="idle",
                    sync_started_at=None
                )
            )

            await session.commit()

        except Exception:
            logger.exception(
                "Failed to clean up sync status for mailbox %s",
                mailbox_id
            )

        raise
