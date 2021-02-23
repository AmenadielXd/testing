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

import motor.motor_asyncio

from alita import DB_URI

# Client to connect to mongodb
mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)


class MongoDB:
    """Class for interacting with Bot database."""

    def __init__(self, collection) -> None:
        self.db = mongodb_client.spam_db  # Test database
        self.collection = self.db[collection]

    # Insert one entry into collection
    async def insert_one(self, document):
        result = await self.collection.insert_one(document)
        return repr(result.inserted_id)

    # Find one entry from collection
    async def find_one(self, query):
        result = await self.collection.find_one(query)
        if result:
            return True
        return False

    # Find entries from collection
    async def find_all(self, query={}):
        lst = []
        async for document in self.collection.find(query):
            lst.append(document)
        return lst

    # Count entries from collection
    async def count(self):
        return await self.collection.count_documents({})

    # Delete entry/entries from collection
    async def delete_one(self, query):
        before_delete = await self.collection.count_documents({})
        await self.collection.delete_many(query)
        after_delete = await self.collection.count_documents({})
        return before_delete, after_delete

    # Replace one entry in collection
    async def replace(self, query, new_data):
        old = await self.collection.find_one(query)
        _id = old["_id"]
        await self.collection.replace_one({"_id": _id}, new_data)
        new = await self.collection.find_one({"_id": _id})
        return old, new
