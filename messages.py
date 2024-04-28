from issaprs import inform_last_heard

HELLO_MSG =  "Welcome! \n\n"

HELP_MSG = (
    "📡 Use /lastheard to see the latest APRS activity on ariss.net.\n\n"
    "🛰️ Use /track if you want to be warned when new APRS activity is "
    "heard by the ISS.\n\n"
    "🤖 Use /why to learn more about how this bot operates."
)

WHY_MSG = (
    "💡 The APRS radio aboard the ISS may not always be active. This bot "
    "alerts you when new APRS activity is detected, providing you with "
    "an opportunity to transmit your packets.\n\nThe bot operates on "
    "the following logic: if there has been a period of six hours or more "
    "without any activity, users will receive a notification once APRS "
    "APRS packets are heard again.\n\n"
    "Use /track to start!"
)

ERROR_MSG = "🤔 Sorry, I didn't understand that command."

ALREADY_MSG = (
    "🤔 You are already tracking APRS activity from the ISS. To stop "
    "tracking, please use /untrack."
)

SUCCESS_MSG = (
    f"🎉 Success\\! You are now tracking the APRS activity from the ISS\\. "
    f"If new activity is detected after six hours of inactivity, you will "
    f"be the first to know\\.\n\n"
    f"You can stop tracking by using /untrack\\.\n\n"
)

NEW_ACTIVITY = "🛰️ New activity detected\\!\n\n"

UNSET_MSG = "🛑 You are no longer tracking APRS activity from the ISS."

UNSET_ERROR_MSG = (
    "🤔 Sorry, but you are not currently tracking APRS activity from the "
    "ISS. To start, use /track."
)
