#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.

"""
A bot to track APRS packets from the ISS.

This Bot uses the Application class to handle the bot and the JobQueue to
send timed messages. A custom library is used to scrape ariss.net, process
its information and prepare user messages.
"""

# Imports
import logging

from telegram import Update
from telegram.ext import PicklePersistence, filters, Application, CommandHandler, MessageHandler, ContextTypes

import issaprs as iss
from config import BOT_KEY
from messages import *

# Configuration
INTERVAL = 60
INACTIVE_TIME = float(6 * iss.HOUR)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a hello message and explanation on how to use the bot."""
    text = HELLO_MSG + HELP_MSG
    await update.message.reply_text(text)


async def helpme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text(HELP_MSG)


async def why(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the rationale behind the creation of the bot."""
    await update.message.reply_text(WHY_MSG)


async def send_last_heard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends information about the latest APRS activity heard by the ISS."""
    await update.message.reply_markdown_v2(iss.inform_last_heard())


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    await update.message.reply_text(ERROR_MSG)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def warn(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an update if there is new APRS activity from the ISS."""
    job = context.job
    inactivity_gap = job.data

    if iss.check_activity(str(job.user_id), inactivity_gap):
        text = NEW_ACTIVITY
        text += iss.inform_last_heard()

        await context.bot.send_message(job.chat_id,
                                       text,
                                       parse_mode="MarkdownV2")


async def set_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a warning to the job queue."""
    inactivity_gap =  int(context.args[0]) if context.args else INACTIVE_TIME
    chat_id = update.effective_message.chat_id
    user_id = update.message.from_user.id
    current_jobs = context.job_queue.get_jobs_by_name("track_" + str(chat_id))

    if current_jobs:
        await update.effective_message.reply_text(ALREADY_MSG)
        return

    context.job_queue.run_repeating(warn,
                                    INTERVAL,
                                    chat_id=chat_id,
                                    user_id=user_id,
                                    name="track_" + str(chat_id),
                                    data=inactivity_gap)

    text = SUCCESS_MSG + iss.inform_last_heard()

    await update.effective_message.reply_markdown_v2(text)


async def unset_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a job from the queue and deletes user database."""
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    job_removed = remove_job_if_exists("track_" + str(chat_id), context)
    text = UNSET_MSG if job_removed else UNSET_ERROR_MSG

    if job_removed:
        iss.delete_user_db(str(user_id))

    await update.message.reply_text(text)


def main() -> None:
    """Run bot."""

    persistence = PicklePersistence(filepath="iss_aprs_bot_persistence")
    app = (Application.builder()
           .token(BOT_KEY)
           .persistence(persistence=persistence)
           .build()
           )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", helpme))
    app.add_handler(CommandHandler("why", why))
    app.add_handler(CommandHandler("lastheard", send_last_heard))
    app.add_handler(CommandHandler("track", set_tracking))
    app.add_handler(CommandHandler(["untrack", "stop"], unset_tracking))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
