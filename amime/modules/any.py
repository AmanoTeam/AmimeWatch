# MIT License
#
# Copyright (c) 2021 Andriel Rodrigues for Amano Team
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
from pyrogram.types import CallbackQuery, InlineQuery, Message

from amime.amime import Amime
from amime.database import Chats, Users


@Amime.on_message(group=-1)
async def set_language_message(bot: Amime, message: Message):
    chat = message.chat
    user = message.from_user
    if not user:
        return
    lang = message._lang
    code: str = ""
    user_code = user.language_code or "en"
    if "." in user_code:
        user_code = user_code.split(".")[0]
    if user_code not in lang.strings.keys():
        user_code = "en"

    if await filters.private(bot, message):
        code = (
            await Users.get_or_create(
                {
                    "name": user.first_name,
                    "username": user.username or "",
                    "language_bot": user_code,
                    "language_anime": user_code,
                    "is_collaborator": False,
                },
                id=user.id,
            )
        )[0].language_bot
    else:
        code = (
            await Chats.get_or_create(
                {
                    "title": chat.title,
                    "username": chat.username or "",
                    "language": "en",
                },
                id=chat.id,
            )
        )[0].language
    message._lang = lang.get_language(code)


@Amime.on_callback_query(group=-1)
async def set_language_callback(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    if not user:
        return
    lang = callback._lang
    code: str = ""
    user_code = user.language_code or "en"
    if "." in user_code:
        user_code = user_code.split(".")[0]
    if user_code not in lang.strings.keys():
        user_code = "en"

    if await filters.private(bot, message):
        code = (
            await Users.get_or_create(
                {
                    "name": user.first_name,
                    "username": user.username or "",
                    "language_bot": user_code,
                    "language_anime": user_code,
                    "is_collaborator": False,
                },
                id=user.id,
            )
        )[0].language_bot
    else:
        code = (
            await Chats.get_or_create(
                {
                    "title": chat.title,
                    "username": chat.username or "",
                    "language": "en",
                },
                id=chat.id,
            )
        )[0].language
    callback._lang = lang.get_language(code)


@Amime.on_inline_query(group=-1)
async def set_language_inline_query(bot: Amime, inline_query: InlineQuery):
    user = inline_query.from_user
    if not user:
        return
    lang = inline_query._lang
    code: str = ""
    user_code = user.language_code or "en"
    if "." in user_code:
        user_code = user_code.split(".")[0]
    if user_code not in lang.strings.keys():
        user_code = "en"

    code = (
        await Users.get_or_create(
            {
                "name": user.first_name,
                "username": user.username or "",
                "language_bot": user_code,
                "language_anime": user_code,
                "is_collaborator": False,
            },
            id=user.id,
        )
    )[0].language_bot
    inline_query._lang = lang.get_language(code)


@Amime.on_message(filters.edited)
async def edited(bot: Amime, message: Message):
    message.stop_propagation()
