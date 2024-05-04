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
Automatically scrapes http://ariss.net to detect new APRS activity
from the ISS.
"""

import csv
import os
import time
import threading
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ARISS last stations heard via ISS page
PAGE = "http://ariss.net?absolute=1"

# Minute, hour and day in seconds:
SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60
DAY = HOUR * 24

# Automatic checker options
INTERVAL = 5 * SECOND
INACTIVE_TIME = float(5 * SECOND)

# Database options
NO_USER = 'testing'
DB_DIR = 'db/'


# Scrapping functions
def get_last_heard() -> list[str]:
    """Scrapes latest APRS activity heard from the ISS. Returns the
    last station heard as an array with strings representing the
    callsign, time, and findU.com URL."""
    soup = BeautifulSoup(requests.get(PAGE).text, 'html.parser')
    rows = soup.find_all('tr')
    last_heard = rows[1].find_all('td')
    callsign = last_heard[0].text.strip()
    timestamp = last_heard[4].text.strip()

    try:
        link = last_heard[0].find('a').get('href')
    except AttributeError:
        link = ''

    return [callsign, timestamp, link]


def calculate_elapsed_time(timestamp: str) -> float:
    """Parses time in the format year, month, day, hour, minutes, and
    seconds, and returns a float of how many seconds have passed."""
    parsed_time = datetime.strptime(timestamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    time_delta = current_time - parsed_time
    return time_delta.total_seconds()


def print_elapsed_time(delta_in_sec: float) -> str:
    """Returns a string of how much time has elapsed since an event,
    e.g., "1 second ago", "10 minutes ago", "8 days ago"."""

    # Parse seconds
    if delta_in_sec == SECOND:
        return "1 second"
    if delta_in_sec < MINUTE:
        return f"{round(delta_in_sec)} seconds"

    # Parse minutes
    if delta_in_sec < HOUR:
        delta_in_min = round(delta_in_sec / MINUTE)
        if delta_in_min == 1:
            return "1 minute"
        if delta_in_min > 1:
            return f"{delta_in_min} minutes"

    # Parse hours
    if delta_in_sec < DAY:
        delta_in_hour = round(delta_in_sec / HOUR)
        if delta_in_hour == 1:
            return "1 hour"
        if delta_in_hour > 1:
            return f"{delta_in_hour} hours"

    # Parse days
    if delta_in_sec > DAY:
        delta_in_day = round(delta_in_sec / DAY)
        if delta_in_day == 1:
            return "1 day"
        if delta_in_day > 1:
            return f"{delta_in_day} days"


def inform_last_heard() -> str:
    """Returns a string informing what station was last heard by the
    ISS on APRS and how long ago that was. The string includes a
    Markdown-style link to findu.com."""
    last_heard = get_last_heard()
    callsign = last_heard[0]
    timestamp = last_heard[1]
    elapsed_time = calculate_elapsed_time(timestamp)
    link = last_heard[2]

    output = f"The last station heard was *{callsign}, "
    output += f"{print_elapsed_time(elapsed_time)} ago*. "
    output += f"See details at [findu.com]({link})." if link else ""
    output = output.replace("-", "\\-").replace(".", "\\.")

    return output


# Database functions
def is_entry_in_db(db_path: str, entry: list) -> bool:
    """Returns if the latest entry in the database is the same as the
    current entry."""
    if not os.path.isfile(db_path):
        return False

    with open(db_path, 'r', encoding = 'UTF-8') as csvfile:
        reader = csv.reader(csvfile)
        last_line = None

        for row in reader:
            last_line = row
        return last_line == entry


def save_last_heard(db_path: str, current: list) -> None:
    """Saves the current last heard station in the database."""
    if not is_entry_in_db(db_path, current):
        with open(db_path, 'a', encoding = 'UTF-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(current)


def read_previously_heard(db_path: str) -> list[str]:
    """Returns the previously last heard station from the database. If
    nothing was found, returns an empty list."""
    with open(db_path, 'r',  encoding = 'UTF-8',) as csvfile:
        reader = csv.reader(csvfile)
        last_line = []

        for row in reader:
            last_line = row
        return last_line


def user_db_path(user: str, db_type: str) -> str:
    """Returns the path to a user's database."""
    user_db = DB_DIR + user + "-" + db_type + '.csv'

    return user_db


def user_has_db(user: str, db_type : str) -> bool:
    """Checks if user has a database file."""
    user_db = user_db_path(user, db_type)

    return os.path.isfile(user_db)


def create_db_for_user(user: str, current: list, db_type: str) -> None:
    "Initializes the user's database with the current station."
    user_db = user_db_path(user, db_type)

    print(f"Log: Initializing ISS APRS database for {user}.")
    save_last_heard(user_db, current)


def delete_user_db(user: str, db_type: str) -> None:
    """Given a user, delete its database file."""
    if user_has_db(user, db_type):
        user_db = user_db_path(user, db_type)
        print(f"Deleting user {user} database…")
        os.remove(user_db)


# Activity checking and reporting
def new_activity(previous: list, current: list, threshold: float) -> bool:
    """Determines if there has been new APRS activity from the ISS
    heard after some time of inactivity."""
    elapsed_time = calculate_elapsed_time(previous[1])

    if previous != current:
        if elapsed_time > threshold:
            return True

    return False


# Tracking
def check_activity(user: str, threshold: float) -> bool:
    """Returns whether new APRS activity from the ISS has been
    detected."""
    print(f"{datetime.now()}: Checking…")

    db_type = "track"
    user_db = user_db_path(user, db_type)
    current_station = get_last_heard()

    if not user_has_db(user, db_type):
        create_db_for_user(user, current_station, db_type)

    previous_station = read_previously_heard(user_db)

    if new_activity(previous_station, current_station, threshold):
        print(f"{datetime.now()}: New ISS APRS activity!")
        print(inform_last_heard())
        save_last_heard(user_db, current_station)

        return True

    print(f"{datetime.now()}: Nothing new…")
    save_last_heard(user_db, current_station)

    return False


# Watching
def was_callsign_heard(user: str, callsign: str) -> bool:
    """Returns whether a callsign's packet was digipeated by the
    ISS."""
    db_type = "watch"
    user_db = user_db_path(user, db_type)
    current_station = get_last_heard()
    current_callsign = current_station[0]
    threshold = SECOND

    if not user_has_db(user, db_type):
        create_db_for_user(user, current_station, db_type)

    previous_station = read_previously_heard(user_db)

    if new_activity(previous_station, current_station, threshold):
        if current_callsign == callsign:
            save_last_heard(user_db, current_station)

            return True

    save_last_heard(user_db, current_station)
    return False


# Functionality testing
def periodically_check_activity() -> None:
    """Runs the tracking routine indefinitely. Useful in testing."""
    while True:
        check_activity(NO_USER, INACTIVE_TIME)
        time.sleep(INTERVAL)


def main() -> None:
    print(inform_last_heard())

    thread = threading.Thread(target=periodically_check_activity)
    # thread.daemon = True
    thread.start()


if __name__ == "__main__":
    main()
