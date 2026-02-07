"""Database operations for scheduled messages.

This module provides helper functions for managing scheduled message records,
including upsert, retrieval, and deletion operations.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from src.db import MessageType, ScheduledMessage, async_session


async def upsert_scheduled_message(
    message_type: MessageType,
    channel_id: str,
    message_id: str,
) -> None:
    """Insert or update a scheduled message record.

    Args:
        message_type: Type of scheduled message (DAILY, WEEKLY, BOSS_SUMMARY)
        channel_id: Discord channel ID where message was posted
        message_id: Discord message ID of the posted message

    Raises:
        Exception: If database operation fails
    """
    try:
        async with async_session() as db:
            stmt = (
                insert(ScheduledMessage)
                .values(
                    type=message_type,
                    channel_id=channel_id,
                    message_id=message_id,
                    created_at=datetime.now(timezone.utc),
                )
                .on_conflict_do_update(
                    index_elements=["type", "channel_id"],
                    set_={
                        "message_id": message_id,
                        "created_at": datetime.now(timezone.utc),
                    },
                )
            )
            await db.execute(stmt)
            await db.commit()
            logging.debug(
                "[scheduled_message_ops] upserted %s message for channel %s",
                message_type,
                channel_id,
            )
    except Exception as e:
        logging.error(
            "[scheduled_message_ops] failed to upsert message: %s", e, exc_info=True
        )
        raise


async def get_scheduled_message(
    message_type: MessageType,
    channel_id: str,
) -> str | None:
    """Get message ID for a given type and channel.

    Args:
        message_type: Type of scheduled message to retrieve
        channel_id: Discord channel ID to look up

    Returns:
        Message ID if found, None otherwise
    """
    try:
        async with async_session() as db:
            stmt = select(ScheduledMessage.message_id).where(
                ScheduledMessage.type == message_type,
                ScheduledMessage.channel_id == channel_id,
            )
            result = await db.execute(stmt)
            message_id = result.scalar_one_or_none()
            if message_id:
                logging.debug(
                    "[scheduled_message_ops] found %s message %s in channel %s",
                    message_type,
                    message_id,
                    channel_id,
                )
            return message_id
    except Exception as e:
        logging.error(
            "[scheduled_message_ops] failed to get message: %s", e, exc_info=True
        )
        return None


async def delete_scheduled_message(
    message_type: MessageType,
    channel_id: str,
) -> None:
    """Delete a scheduled message record from the database.

    Args:
        message_type: Type of scheduled message to delete
        channel_id: Discord channel ID to delete from
    """
    try:
        async with async_session() as db:
            stmt = delete(ScheduledMessage).where(
                ScheduledMessage.type == message_type,
                ScheduledMessage.channel_id == channel_id,
            )
            await db.execute(stmt)
            await db.commit()
            logging.debug(
                "[scheduled_message_ops] deleted %s message record for channel %s",
                message_type,
                channel_id,
            )
    except Exception as e:
        logging.error(
            "[scheduled_message_ops] failed to delete message: %s", e, exc_info=True
        )
