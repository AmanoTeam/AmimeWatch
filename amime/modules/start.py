# MIT License
#
# Copyright (c) 2021 Amano Team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb
from typing import Union

from ..amime import Amime
from ..database import Chats, Users
from .help import help_union, help_module_union
from .anime.view import view_anime
from .manga.view import view_manga


@Amime.on_message(filters.cmd(r"start$"))
async def start_message(bot: Amime, message: Message):
    lang = message._lang

    if await filters.private(bot, message):
        await start_union(bot, message)
    else:
        await message.reply_text(
            lang.start_in_pm,
            reply_markup=ikb(
                [
                    [
                        (
                            lang.start_button,
                            f"https://t.me/{bot.me.username}?start=",
                            "url",
                        )
                    ]
                ]
            ),
        )


@Amime.on_callback_query(filters.regex(r"^start$"))
async def start_callback(bot: Amime, callback: CallbackQuery):
    await start_union(bot, callback)


async def start_union(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    lang = union._lang

    keyboard = [
        [(lang.help_button, "help"), (lang.about_button, "about")],
        [(lang.favorites_button, "favorites"), (lang.settings_button, "settings")],
        [
            (lang.group_button, "https://t.me/AmimeWatchGroup", "url"),
            (lang.channel_button, "https://t.me/AmimeWatch", "url"),
        ],
        [(lang.search_button, "!a ", "switch_inline_query_current_chat")],
    ]
    user = union.from_user

    await (union.edit_message_text if is_callback else union.reply_text)(
        lang.start.format(
            mention=user.mention(),
            bot_name=bot.me.first_name,
            anilist="<a href='https://anilist.co'>Anilist</a>",
        ),
        reply_markup=ikb(keyboard),
        disable_web_page_preview=True,
    )


@Amime.on_message(filters.cmd(r"start help$") & filters.private)
async def start_help_message(bot: Amime, message: Message):
    await help_union(bot, message)


@Amime.on_message(filters.cmd(r"start help_(?P<module>.+)") & filters.private)
async def start_help_module_message(bot: Amime, message: Message):
    await help_module_union(bot, message)


@Amime.on_message(filters.new_chat_members & filters.group)
async def new_members_message(bot: Amime, message: Message):
    chat = message.chat
    members = message.new_chat_members
    for member in members:
        if member.id == bot.me.id and member.username == bot.me.username:
            if len(await Chats.filter(id=chat.id)) == 0:
                await Chats.create(
                    id=chat.id,
                    title=chat.title,
                    username=chat.username or "",
                    language="en",
                )


@Amime.on_message(filters.cmd(r"start (?P<type>anime|manga)_(?P<id>\d+)"))
async def view_content(bot: Amime, message: Message):
    content_type = message.matches[0]["type"]
    content_id = int(message.matches[0]["id"])

    message.matches = [{"id": content_id}]

    if content_type == "anime":
        await view_anime(bot, message)
    else:
        await view_manga(bot, message)
