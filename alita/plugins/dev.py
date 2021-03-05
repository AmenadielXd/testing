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


import sys
from asyncio import create_subprocess_shell, subprocess
from io import BytesIO, StringIO
from time import gmtime, strftime, time
from traceback import format_exc

from pyrogram import filters
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    MessageTooLong,
    PeerIdInvalid,
    RPCError,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from speedtest import Speedtest
from ujson import dumps

from alita import DEV_PREFIX_HANDLER, LOGFILE, LOGGER, MESSAGE_DUMP, UPTIME
from alita.bot_class import Alita
from alita.database.chats_db import Chats
from alita.tr_engine import tlang
from alita.utils.aiohttp_helper import AioHttp
from alita.utils.custom_filters import dev_filter
from alita.utils.parser import mention_markdown
from alita.utils.paste import paste
from alita.utils.redis_helper import allkeys, flushredis, get_key

# initialise database
chatdb = Chats()


@Alita.on_message(filters.command("logs", DEV_PREFIX_HANDLER) & dev_filter)
async def send_log(c: Alita, m: Message):

    replymsg = await m.reply_text("Sending logs...!")
    await c.send_message(
        MESSAGE_DUMP,
        f"#LOGS\n\n**User:** {(await mention_markdown(m.from_user.first_name, m.from_user.id))}",
    )
    # Send logs
    with open(LOGFILE) as f:
        raw = (await paste(f.read()))[1]
    await m.reply_document(
        document=LOGFILE,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Logs", url=raw)]],
        ),
        quote=True,
    )
    await replymsg.delete()
    return


@Alita.on_message(filters.command("speedtest", DEV_PREFIX_HANDLER) & dev_filter)
async def test_speed(c: Alita, m: Message):

    await c.send_message(
        MESSAGE_DUMP,
        f"#SPEEDTEST\n\n**User:** {(await mention_markdown(m.from_user.first_name, m.from_user.id))}",
    )
    sent = await m.reply_text(await tlang(m, "dev.speedtest.start_speedtest"))
    s = Speedtest()
    bs = s.get_best_server()
    dl = round(s.download() / 1024 / 1024, 2)
    ul = round(s.upload() / 1024 / 1024, 2)
    await sent.edit_text(
        (await tlang(m, "dev.speedtest.speedtest_txt")).format(
            host=bs["sponsor"],
            ping=int(bs["latency"]),
            download=dl,
            upload=ul,
        ),
    )
    return


@Alita.on_message(filters.command("neofetch", DEV_PREFIX_HANDLER) & dev_filter)
async def neofetch_stats(_, m: Message):
    cmd = "neofetch --stdout"

    process = await create_subprocess_shell(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e = stderr.decode()
    if not e:
        e = "No Error"
    OUTPUT = stdout.decode()
    if not OUTPUT:
        OUTPUT = "No Output"

    try:
        await m.reply_text(OUTPUT, quote=True)
    except MessageTooLong:
        with BytesIO(str.encode(OUTPUT)) as f:
            f.name = "neofetch.txt"
            await m.reply_document(document=f, caption="neofetch result")
        await m.delete()
    return


@Alita.on_message(filters.command(["eval", "py"], DEV_PREFIX_HANDLER) & dev_filter)
async def evaluate_code(c: Alita, m: Message):

    if len(m.text.split()) == 1:
        await m.reply_text(await tlang(m, "dev.execute_cmd_err"))
        return
    sm = await m.reply_text("`Processing...`")
    cmd = m.text.split(None, maxsplit=1)[1]

    reply_to_id = m.message_id
    if m.reply_to_message:
        reply_to_id = m.reply_to_message.message_id

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec(cmd, c, m)
    except BaseException as ef:
        LOGGER.error(ef)
        exc = format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    final_output = f"<b>EVAL</b>: <code>{cmd}</code>\n\n<b>OUTPUT</b>:\n<code>{evaluation.strip()}</code> \n"

    try:
        await sm.edit(final_output)
    except MessageTooLong:
        with BytesIO(str.encode(final_output)) as f:
            f.name = "py.txt"
            await m.reply_document(
                document=f,
                caption=cmd,
                disable_notification=True,
                reply_to_message_id=reply_to_id,
            )
        await sm.delete()

    return


async def aexec(code, c, m):
    exec("async def __aexec(c, m): " + "".join(f"\n {l}" for l in code.split("\n")))
    return await locals()["__aexec"](c, m)


@Alita.on_message(filters.command(["exec", "sh"], DEV_PREFIX_HANDLER) & dev_filter)
async def execution(_, m: Message):

    if len(m.text.split()) == 1:
        await m.reply_text(await tlang(m, "dev.execute_cmd_err"))
        return
    sm = await m.reply_text("`Processing...`")
    cmd = m.text.split(maxsplit=1)[1]
    reply_to_id = m.message_id
    if m.reply_to_message:
        reply_to_id = m.reply_to_message.message_id

    process = await create_subprocess_shell(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e = stderr.decode()
    if not e:
        e = "No Error"
    o = stdout.decode()
    if not o:
        o = "No Output"

    OUTPUT = ""
    OUTPUT += f"<b>QUERY:</b>\n<u>Command:</u>\n<code>{cmd}</code> \n"
    OUTPUT += f"<u>PID</u>: <code>{process.pid}</code>\n\n"
    OUTPUT += f"<b>stderr</b>: \n<code>{e}</code>\n\n"
    OUTPUT += f"<b>stdout</b>: \n<code>{o}</code>"

    try:
        await sm.edit_text(OUTPUT)
    except MessageTooLong:
        with BytesIO(str.encode(OUTPUT)) as f:
            f.name = "sh.txt"
            await m.reply_document(
                document=f,
                caption=cmd,
                disable_notification=True,
                reply_to_message_id=reply_to_id,
            )
        await sm.delete()
    return


@Alita.on_message(filters.command("ip", DEV_PREFIX_HANDLER) & dev_filter)
async def public_ip(c: Alita, m: Message):

    ip = (await AioHttp.get_text("https://api.ipify.org"))[0]
    await c.send_message(
        MESSAGE_DUMP,
        f"#IP\n\n**User:** {(await mention_markdown(m.from_user.first_name, m.from_user.id))}",
    )
    await m.reply_text(
        (await tlang(m, "dev.bot_ip")).format(ip=f"<code>{ip}</code>"),
        quote=True,
    )
    return


@Alita.on_message(filters.command("chatlist", DEV_PREFIX_HANDLER) & dev_filter)
async def chats(c: Alita, m: Message):
    exmsg = await m.reply_text(await tlang(m, "dev.chatlist.exporting"))
    await c.send_message(
        MESSAGE_DUMP,
        f"#CHATLIST\n\n**User:** {(await mention_markdown(m.from_user.first_name, m.from_user.id))}",
    )
    all_chats = (await chatdb.list_chats()) or []
    chatfile = await tlang(m, "dev.chatlist.header")
    P = 1
    for chat in all_chats:
        try:
            chat_info = await c.get_chat(int(chat["chat_id"]))
            chat_members = chat_info.members_count
            try:
                invitelink = chat_info.invite_link
            except KeyError:
                invitelink = "No Link!"
            chatfile += "{}. {} | {} | {} | {}\n".format(
                P,
                chat["chat_name"],
                chat["chat_id"],
                chat_members,
                invitelink,
            )
            P += 1
        except ChatAdminRequired:
            pass
        except ChannelPrivate:
            await chatdb.remove_chat(chat.chat_id)
        except PeerIdInvalid:
            LOGGER.warning(f"Peer  not found {chat.chat_id}")
        except RPCError as ef:
            LOGGER.error(ef)
            await m.reply_text(f"**Error:**\n{ef}")

    with BytesIO(str.encode(chatfile)) as f:
        f.name = "chatlist.txt"
        await m.reply_document(
            document=f,
            caption=(await tlang(m, "dev.chatlist.chats_in_db")),
        )
    await exmsg.delete()
    return


@Alita.on_message(filters.command("uptime", DEV_PREFIX_HANDLER) & dev_filter)
async def uptime(_, m: Message):
    up = strftime("%Hh %Mm %Ss", gmtime(time() - UPTIME))
    await m.reply_text((await tlang(m, "dev.uptime")).format(uptime=up), quote=True)
    return


@Alita.on_message(filters.command("alladmins", DEV_PREFIX_HANDLER) & dev_filter)
async def list_all_admins(_, m: Message):

    replymsg = await m.reply_text(
        (await tlang(m, "dev.alladmins.getting_admins")),
        quote=True,
    )
    len_admins = 0  # Total number of admins

    admindict = await get_key("ADMINDICT")

    for i in list(admindict.values()):
        len_admins += len(i)

    try:
        await replymsg.edit_text(
            (await tlang(m, "dev.alladmins.admins_i_know_str")).format(
                len_admins=len_admins,
                admindict=str(admindict),
            ),
        )
    except MessageTooLong:
        raw = (await paste(admindict))[1]
        with BytesIO(str.encode(dumps(admindict, indent=2))) as f:
            f.name = "allAdmins.txt"
            await m.reply_document(
                document=f,
                caption=(await tlang(m, "dev.alladmins.admins_in_cache")).format(
                    len_admins=len_admins,
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                (await tlang(m, "dev.alladmins.alladmins_btn")),
                                url=raw,
                            ),
                        ],
                    ],
                ),
            )
        await replymsg.delete()

    return


@Alita.on_message(filters.command("rediskeys", DEV_PREFIX_HANDLER) & dev_filter)
async def show_redis_keys(_, m: Message):
    txt_dict = {}
    replymsg = await m.reply_text("Fetching Redis Keys...", quote=True)
    keys = await allkeys()
    for i in keys:
        txt_dict[i] = await get_key(str(i))
    try:
        if not txt_dict:
            return replymsg.edit_text("No keys stored in redis!")
        await replymsg.edit_text(str(txt_dict))
    except MessageTooLong:
        raw = (await paste(txt_dict))[1]
        with BytesIO(str.encode(dumps(txt_dict, indent=2))) as f:
            f.name = "redisKeys.txt"
            await m.reply_document(
                document=f,
                caption="Here are all the Redis Keys I know.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Redis Keys", url=raw)]],
                ),
            )
        await replymsg.delete()
    return


@Alita.on_message(filters.command("flushredis", DEV_PREFIX_HANDLER) & dev_filter)
async def flush_redis(_, m: Message):
    replymsg = await m.reply_text(
        (await tlang(m, "dev.flush_redis.flushing_redis")),
        quote=True,
    )
    try:
        await flushredis()
        await replymsg.edit_text(await tlang(m, "dev.flush_redis.flushed_redis"))
    except BaseException as ef:
        LOGGER.error(ef)
        await replymsg.edit_text(await tlang(m, "dev.flush_redis.flush_failed"))
    return


@Alita.on_message(filters.command("leavechat", DEV_PREFIX_HANDLER) & dev_filter)
async def leave_chat(c: Alita, m: Message):
    if len(m.text.split()) != 2:
        await m.reply_text("Supply a chat id which I should leave!", quoet=True)
        return

    chat_id = m.text.split(None, 1)[1]

    replymsg = await m.reply_text(f"Trying to leave chat {chat_id}...", quote=True)
    try:
        await c.send_message(chat_id, "Bye everyone!")
        await c.leave_chat(chat_id)
        await replymsg.edit_text(f"Left <code>{chat_id}</code>.")
    except PeerIdInvalid:
        await replymsg.edit_text("Haven't seen this group in this session")
    except RPCError as ef:
        LOGGER.error(ef)
        await replymsg.edit_text(f"Failed to leave chat!\nError: <code>{ef}</code>.")
    return
