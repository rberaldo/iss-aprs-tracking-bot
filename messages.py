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
Messages used by the ISS APRS tracking bot.
"""

HELLO_MSG =  "Welcome! \n\n"

HELP_MSG = (
    "📡 Use /lastheard to see the latest APRS activity on ariss.net.\n\n"
    "🛰️ Use /track if you want to be warned when new APRS activity is "
    "heard by the ISS.\n\n"
    "👩‍🚀 Use /watch <callsign> to receive a notification when APRS "
    "packets from a specific callsign is heard. Do not forget to include "
    "the SSID.\n\n"
    "🤖 Use /why to learn more about how this bot operates."
)

WHY_MSG = (
    "💡 The APRS radio aboard the ISS may not always be active. This bot "
    "alerts you when new APRS activity is detected, providing you with "
    "an opportunity to transmit your packets.\n\n/track operates on "
    "the following logic: if there has been a period of six hours or more "
    "without any activity, users will receive a notification once APRS "
    "packets are heard again.\n\n"
    "/watch <callsign> notifies when activity from the given callsign is "
    "heard. The bot checks every five seconds.\n\n"
    "This bot is developed by Rafael PU2URT. Visit aprs.tools for a "
    "cool APRS symbol searcher.\n\n"
    "73!"
)

SUCCESS_TRACK_MSG = (
    f"🎉 Success\\! You are now tracking the APRS activity from the ISS\\. "
    f"If new activity is detected after six hours of inactivity, you will "
    f"be the first to know\\.\n\n"
    f"You can stop tracking by using /untrack\\.\n\n"
)

ERROR_MSG = "🤔 Sorry, I didn't understand that command."

ALREADY_TRACK_MSG = (
    "🤔 You are already tracking APRS activity from the ISS. To stop "
    "tracking, please use /untrack."
)

NEW_ACTIVITY = "🛰️ New activity detected\\!\n\n"

UNSET_MSG = "🛑 You are no longer tracking APRS activity from the ISS."

UNSET_ERROR_MSG = (
    "🤔 Sorry, but you are not currently tracking APRS activity from the "
    "ISS. To start, use /track."
)

SUCCESS_WATCH_MSG = (
    "🎉 Success\\! You are now watching for activity from the callsign "
)

STOP_WATCH_MSG = "\n\nTo stop watching, use /unwatch\\."

ALREADY_WATCH_MSG = (
    "🤔 You are already watching a callsign. To stop, please use /unwatch."
)

CALLSIGN_ERROR_MSG = (
    "Usage: /watch <callsign>\n\nDo not forget to include the SSID, "
    "e.g., /watch PU2URT-12."
)

CALLSIGN_ACTIVITY = " has just been digipeated by the ISS\\!"

UNSET_WATCH_MSG = (
    "🛑 You are no longer watching callsign activity from the ISS."
)

UNSET_WATCH_ERROR_MSG = (
    "🤔 Sorry, but you are not currently watching a callsign. "
    "To start, use: /watch <callsign>"
)
