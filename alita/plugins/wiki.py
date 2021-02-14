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


from pyrogram import filters
from pyrogram.types import Message
from wikipedia import summary
from wikipedia.exceptions import DisambiguationError, PageError

from alita import PREFIX_HANDLER
from alita.bot_class import Alita

__PLUGIN__ = "Wikipedia"

__help__ = """
Search Wikipedia on the go in your group!

**Available commands:**
 × /wiki <query>: wiki your query.
"""


@Alita.on_message(filters.command("wiki", PREFIX_HANDLER))
async def wiki(_: Alita, m: Message):
    if m.reply_to_message:
        search = m.reply_to_message.text
    else:
        search = m.text.split(None, 1)[1]
    try:
        res = summary(search)
    except DisambiguationError as de:
        await m.reply_text(
            f"Disambiguated pages found! Adjust your query accordingly.\n<i>{de}</i>",
            parse_mode="html",
        )
        return
    except PageError as pe:
        await m.reply_text(f"<code>{pe}</code>", parse_mode="html")
        return
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", "rb") as f:
                await m.reply_document(
                    document=f,
                    reply_to_message_id=m.message_id,
                    parse_mode="html",
                )
        else:
            await m.reply_text(result, parse_mode="html", disable_web_page_preview=True)

    return
