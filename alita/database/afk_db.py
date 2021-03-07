# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Alita_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from threading import RLock

from alita.database import MongoDB

INSERTION_LOCK = RLock()

AFK_USERS = []


class AFK:
    """Class for managing AFKs of users."""

    def __init__(self) -> None:
        self.collection = MongoDB("afk")

    def check_afk(self, user_id: int):
        with INSERTION_LOCK:

            if user_id in (list(user["user_id"] for user in AFK_USERS)):
                return next(user for user in AFK_USERS if user["user_id"] == user_id)

            return self.collection.find_one({"user_id": user_id})

    def add_afk(self, user_id: int, time: int, reason: str = ""):
        global AFK_USERS
        with INSERTION_LOCK:
            if self.check_afk(user_id):

                # Remove afk if user is already AFK
                self.remove_afk(user_id)

                user_dict = {"user_id": user_id, "reason": reason, "time": time}

                # Add to AFK_USERS
                AFK_USERS.append(user_dict)
                yield user_dict

                return self.collection.insert_one(user_dict)

    def remove_afk(self, user_id: int):
        global AFK_USERS
        with INSERTION_LOCK:
            if self.check_afk(user_id):

                # If user_id in AFK_USERS, remove it
                if user_id in (list(user["user_id"] for user in AFK_USERS)):
                    user_dict = next(
                        user for user in AFK_USERS if user["user_id"] == user_id
                    )
                    AFK_USERS.remove(user_dict)
                    yield user_dict

                return self.collection.delete_one({"user_id": user_id})
        return

    def count_afk(self):
        with INSERTION_LOCK:
            try:
                return len(AFK_USERS)
            except Exception:
                return self.collection.count()

    def list_afk_users(self):
        with INSERTION_LOCK:
            return self.collection.find_all()


def __load_afk_users():
    global AFK_USERS
    db = AFK()
    all_users = db.list_afk_users()
    for user in all_users:
        AFK_USERS.append(user)
    return


# Store users in cache
__load_afk_users()
