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


@Amime.on_message(filters.cmd(r"settings") & filters.private)
async def settings_private_message(bot: Amime, message: Message):
    await settings_union(bot, message)


@Amime.on_message(filters.cmd(r"settings") & filters.group)
async def settings_group_message(bot: Amime, message: Message):
    chat = message.chat
    user = message.from_user
    member = await bot.get_chat_member(chat.id, user.id)
    if member.status in ["administrator", "creator"]:
        await settings_union(bot, message)


@Amime.on_callback_query(filters.regex(r"^settings"))
async def settings_callback(bot: Amime, callback: CallbackQuery):
    await settings_union(bot, callback)


async def settings_union(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    is_private = await filters.private(bot, union.message if is_callback else union)
    lang = union._lang

    keyboard = [
        [(lang.language_button, f"language {'bot' if is_private else 'group'}")]
    ]

    if is_callback and is_private:
        keyboard.append([(lang.back_button, "start")])

    await (union.edit_message_text if is_callback else union.reply_text)(
        lang.settings_private if is_private else lang.settings_group,
        reply_markup=ikb(keyboard),
    )
