from datetime import datetime, timedelta
import logging
from typing import *
import sqlite3
from telegram import ChatPermissions, MessageReactionUpdated, Update
from telegram.ext import Application, MessageReactionHandler, ContextTypes
from kaia.infra.loc import Loc

logger = logging.getLogger("ReactionHandler")


class TriggerCondition:
    """
    Represents a trigger condition for a reaction in the chatbot.
    You can ban user for getting some 💩 and notify all chat users that some message got many 👍
    Attributes:
        emoji (str): The emoji that triggers the condition.
        count (int): The minimum count of the emoji required to trigger the condition.
        message (str, optional): The message associated with the condition. Defaults to None.
        should_ban (bool, optional): Indicates whether the user should be banned if the condition is triggered. Defaults to False.
    """

    def __init__(self, emoji: str, count: int, message=None, should_ban: bool = False):
        self.emoji = emoji
        self.count = count
        self.should_ban = should_ban
        self.message = (
            message if message else f"Это сообщение набрало больше {count} {emoji}"
        )


class ReactionHandler:
    def __init__(
        self,
        application: Application,
        trigger_conditions: List[TriggerCondition],
        ban_duration_hours: int = 12,
        keep_records_days: int = 14,
    ):
        self.app = application
        self.ban_duration_hours = ban_duration_hours
        self.trigger_conditions = trigger_conditions
        self.keep_records_days = keep_records_days
        self.setup_database()
        self.register_handlers()

    def register_handlers(self):
        self.app.add_handler(MessageReactionHandler(self.on_reaction))

    def clear_old_records(self):
        """
        Clears old records from the database to prevent it from growing too large.
        It runs every time the database is set up. Maybe we should run it periodically?
        """

        last_ok_date = datetime.now() - timedelta(days=self.keep_records_days)
        formatted_date = last_ok_date.strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("DELETE FROM reactions WHERE timestamp < ?", (formatted_date,))
        self.cursor.execute(
            "DELETE FROM triggered_messages WHERE timestamp < ?", (formatted_date,)
        )
        self.conn.commit()

    def setup_database(self):
        db_path = Loc.temp_folder / "reactions.db"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_id INTEGER,
            emoji TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS triggered_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        self.clear_old_records()

    def count_emoji(self, chat_id, message_id, emoji):
        """
        Counts the number of times a specific emoji has been used as a reaction to a message.

        Args:
            chat_id (int): The ID of the chat.
            message_id (int): The ID of the message.
            emoji (str): The emoji to count.

        Returns:
            int: The count of the specified emoji for the given chat and message.
        """
        self.cursor.execute(
            "SELECT COUNT(*) FROM reactions WHERE chat_id = ? AND message_id = ? AND emoji = ?",
            (chat_id, message_id, emoji),
        )
        return self.cursor.fetchone()[0]

    def already_triggered(self, chat_id, message_id):
        """
        Checks if a message has already been triggered in a specific chat.

        Args:
            chat_id (int): The ID of the chat.
            message_id (int): The ID of the message.

        Returns:
            bool: True if the message has already been triggered, False otherwise.
        """
        self.cursor.execute(
            "SELECT * FROM triggered_messages WHERE chat_id = ? AND message_id = ?",
            (chat_id, message_id),
        )
        return self.cursor.fetchone() is not None

    async def on_reaction(
        self, update: MessageReactionUpdated, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the event when a reaction is added to a message.

        Args:
            update (MessageReactionUpdated): The update object containing information about the reaction event.
            context (ContextTypes.DEFAULT_TYPE): The context object for handling the reaction event.

        Returns:
            None
        """
        chat_id = update.message_reaction.chat.id
        message_id = update.message_reaction.message_id
        # On every reaction, we delete the old reactions and insert the new ones
        self.cursor.execute(
            "DELETE FROM reactions WHERE chat_id = ? AND message_id = ?",
            (chat_id, message_id),
        )
        for reaction in update.message_reaction.new_reaction:
            self.cursor.execute(
                "INSERT INTO reactions (chat_id, message_id, emoji) VALUES (?, ?, ?)",
                (chat_id, message_id, reaction["emoji"]),
            )
        self.conn.commit()
        # Check if count of any reaction has reached the limit and message has not been triggered yet
        for condition in self.trigger_conditions:
            if self.count_emoji(
                chat_id, message_id, condition.emoji
            ) >= condition.count and not self.already_triggered(chat_id, message_id):
                # Reaction object does not contain the user_id of the user who reacted, so we need to send a message and reply to it
                reply = await context.bot.send_message(
                    chat_id=chat_id,
                    text=condition.message,
                    reply_to_message_id=message_id,
                )
                user_id = reply.reply_to_message.from_user.id
                if condition.should_ban:

                    banned_until = datetime.now() + timedelta(
                        hours=self.ban_duration_hours
                    )
                    logger.info(
                        f"User {user_id} is banned until {banned_until} for triggering reaction {condition.emoji} {condition.count} times"
                    )
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=reply.reply_to_message.from_user.id,
                        until_date=banned_until,
                        permissions=ChatPermissions.no_permissions(),
                    )

                # We insert the message_id of the message that triggered the reaction, so we don't trigger it again
                self.cursor.execute(
                    "INSERT INTO triggered_messages (chat_id, message_id) VALUES (?, ?)",
                    (chat_id, message_id),
                )
                self.conn.commit()
