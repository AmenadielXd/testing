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

WARNS_CACHE = {}


class Warns:
    def __init__(self) -> None:
        self.collection = MongoDB("chat_warns")

    def warn_user(self, chat_id: int, user_id: int, warn_reason=None):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if curr:
                curr_warns = curr["warns"] + [warn_reason]
                num_warns = curr["num_warns"] + 1
                self.collection.update(
                    {"chat_id": chat_id, "user_id": user_id},
                    {"warns": curr_warns, "num_warns": num_warns},
                )
                return curr_warns, num_warns

            self.collection.insert_one(
                {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "warns": [warn_reason],
                    "num_warns": 1,
                },
            )

            return [warn_reason], 1

    def remove_warn(self, chat_id: int, user_id: int):
        with INSERTION_LOCK:

            curr = self.collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if curr:
                curr_warns = curr["warns"][:-1]
                num_warns = curr["num_warns"] - 1
                self.collection.update(
                    {"chat_id": chat_id, "user_id": user_id},
                    {"warns": curr_warns, "num_warns": num_warns},
                )
                return curr_warns, num_warns

            return [], 0

    def reset_warns(self, chat_id: int, user_id: int):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if curr:
                return self.collection.delete_one(
                    {"chat_id": chat_id, "user_id": user_id},
                )
            return True

    def get_warns(self, chat_id: int, user_id: int):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if curr:
                return curr["warns"], curr["num_warns"]
            return [], 0


class WarnSettings:
    def __init__(self) -> None:
        self.collection = MongoDB("chat_warn_settings")

    def get_warnings_settings(self, chat_id: int):
        curr = self.collection.find_one({"_id": chat_id})
        if curr:
            return curr
        curr = {"_id": chat_id, "warn_mode": "kick", "warn_limit": 3}
        self.collection.insert_one(curr)
        return curr

    def set_warnmode(self, chat_id: int, warn_mode: str = "kick"):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"_id": chat_id})
            if curr:
                self.collection.update(
                    {"_id": chat_id},
                    {"warn_mode": warn_mode},
                )
                return warn_mode

            self.collection.insert_one(
                {"_id": chat_id, "warn_mode": warn_mode, "warn_limit": 3},
            )

            return warn_mode

    def get_warnmode(self, chat_id: int):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"_id": chat_id})
            if curr:
                return curr

            self.collection.insert_one(
                {"_id": chat_id, "warn_mode": "kick", "warn_limit": 3},
            )

            return "kick"

    def set_warnlimit(self, chat_id: int, warn_limit: int = 3):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"_id": chat_id})
            if curr:
                self.collection.update(
                    {"_id": chat_id},
                    {"warn_limit": warn_limit},
                )
                return warn_limit

            self.collection.insert_one(
                {"_id": chat_id, "warn_mode": "kick", "warn_limit": warn_limit},
            )

            return warn_limit

    def get_warnlimit(self, chat_id: int):
        with INSERTION_LOCK:
            curr = self.collection.find_one({"_id": chat_id})
            if curr:
                return curr["warn_limit"]

            self.collection.insert_one(
                {"_id": chat_id, "warn_mode": "kick", "warn_limit": 3},
            )

            return 3
