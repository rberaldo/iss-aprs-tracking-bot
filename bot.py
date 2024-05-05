#!/usr/bin/env python
# Copyright 2024 Rafael Beraldo
#
# This file is part of ISS APRS tracking bot.
#
# ISS APRS tracking bot is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# ISS APRS tracking bot is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ISS APRS tracking bot. If not, see
# <https://www.gnu.org/licenses/>.
#
"""
A bot to track APRS packet activity from the ISS.
"""

# Imports
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, PicklePersistence, filters, ContextTypes
from ptbcontrib.ptb_jobstores.mongodb import PTBMongoDBJobStore

import issaprs as iss
from config import TEST_BOT_KEY, MONGO_DB_URI
from messages import *

# Configuration
TRACK_INTERVAL = 60
WATCH_INTERVAL = 5
INACTIVE_TIME = float(6 * iss.HOUR)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a hello message and the bot usage instructions."""
    text = HELLO_MSG + HELP_MSG
    await update.message.reply_text(text)


async def helpme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the bot usage instructions."""
    await update.message.reply_text(HELP_MSG)


async def why(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an explanation about how the bot operates."""
    await update.message.reply_text(WHY_MSG)


async def send_last_heard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends information about the latest APRS packet from the ISS."""
    await update.message.reply_markdown_v2(iss.inform_last_heard())


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    await update.message.reply_text(ERROR_MSG)


# Job handlers
def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


# Tracking: update user when new activity is heard
async def warn(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an update if there is new APRS activity from the ISS after
    a given gap of inactivity. The default is given by INACTIVE_TIME."""
    job = context.job
    inactivity_gap = job.data

    if iss.check_activity(str(job.user_id), inactivity_gap):
        text = NEW_ACTIVITY
        text += iss.inform_last_heard()

        await context.bot.send_message(job.chat_id,
                                       text,
                                       parse_mode="MarkdownV2")


async def set_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a tracking job to the queue."""
    chat_id = update.effective_message.chat_id
    user_id = update.message.from_user.id
    job_name = "track_" + str(chat_id)
    inactivity_gap =  float(context.args[0]) if context.args else INACTIVE_TIME
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if current_jobs:
        await update.effective_message.reply_text(ALREADY_TRACK_MSG)
        return

    context.job_queue.run_repeating(warn,
                                    TRACK_INTERVAL,
                                    chat_id=chat_id,
                                    user_id=user_id,
                                    name=job_name,
                                    data=inactivity_gap)

    text = SUCCESS_TRACK_MSG + iss.inform_last_heard()
    await update.effective_message.reply_markdown_v2(text)


async def unset_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a job from the queue and deletes user database."""
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    job_name = "track_" + str(chat_id)
    job_removed = remove_job_if_exists(job_name, context)
    text = UNSET_MSG if job_removed else UNSET_ERROR_MSG

    if job_removed:
        iss.delete_user_db(str(user_id), "track")

    await update.message.reply_text(text)


# Watching: listen for activity from a given callsign
async def watch(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an update if there is new activity from a specific callsign."""
    job = context.job
    callsign = job.data

    if iss.was_callsign_heard(str(job.user_id), callsign):
        text = NEW_ACTIVITY
        text += "*" + callsign.replace("-", "\\-") + "*"
        text += CALLSIGN_ACTIVITY

        await context.bot.send_message(job.chat_id,
                                       text,
                                       parse_mode="MarkdownV2")


async def set_watching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a watching job to the queue."""
    chat_id = update.effective_message.chat_id
    user_id = update.message.from_user.id
    job_name = "watch_" + str(chat_id)
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    try:
        callsign = context.args[0]
        callsign = callsign.upper()

        if current_jobs:
            await update.effective_message.reply_text(ALREADY_WATCH_MSG)
            return

        context.job_queue.run_repeating(watch,
                                        WATCH_INTERVAL,
                                        chat_id=chat_id,
                                        user_id=user_id,
                                        name=job_name,
                                        data=callsign)

        text = SUCCESS_WATCH_MSG
        text += "*" + callsign.replace("-", "\\-") + "*\\. "
        text += STOP_WATCH_MSG
        await update.effective_message.reply_markdown_v2(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text(CALLSIGN_ERROR_MSG)


async def unset_watching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a watch job from the queue."""
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    job_name = "watch_" + str(chat_id)
    job_removed = remove_job_if_exists(job_name, context)
    text = UNSET_WATCH_MSG if job_removed else UNSET_WATCH_ERROR_MSG

    if job_removed:
        iss.delete_user_db(str(user_id), "watch")

    await update.message.reply_text(text)


# Main loop
def main() -> None:
    """Run bot."""

    # Setup bot and persistence
    persistence = PicklePersistence(filepath="iss_aprs_bot_persistence")
    app = (Application.builder()
           .token(TEST_BOT_KEY)
           .persistence(persistence=persistence)
           .build()
           )

    app.job_queue.scheduler.add_jobstore(
        PTBMongoDBJobStore(
            application=app,
            host=MONGO_DB_URI,
        )
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", helpme))
    app.add_handler(CommandHandler("why", why))
    app.add_handler(CommandHandler("lastheard", send_last_heard))
    app.add_handler(CommandHandler("track", set_tracking))
    app.add_handler(CommandHandler(["untrack", "stop"], unset_tracking))
    app.add_handler(CommandHandler("watch", set_watching))
    app.add_handler(CommandHandler("unwatch", unset_watching))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
