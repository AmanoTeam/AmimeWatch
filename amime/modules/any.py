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

from ..amime import Amime
from ..database import Chats, Users


@Amime.on_message(group=-1)
async def set_language_message(bot: Amime, message: Message):
    chat = message.chat
    user = message.from_user
    lang = message._lang
    code: str = ""

    if await filters.private(bot, message):
        if len(await Users.filter(id=user.id)) == 0:
            await Users.create(
                id=user.id,
                name=user.first_name,
                username=user.username or "",
                language_bot="en",
                language_anime="en",
                is_collaborator=False,
            )

        code = (await Users.get(id=message.from_user.id)).language_bot
    else:
        if len(await Chats.filter(id=chat.id)) == 0:
            await Chats.create(
                id=chat.id,
                title=chat.title,
                username=chat.username or "",
                language="en",
            )

        code = (await Chats.get(id=message.chat.id)).language
    message._lang = lang.get_language(code)


@Amime.on_callback_query(group=-1)
async def set_language_callback(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang
    code: str = ""

    if await filters.private(bot, message):
        if len(await Users.filter(id=user.id)) == 0:
            await Users.create(
                id=user.id,
                name=user.first_name,
                username=user.username or "",
                language_bot="en",
                language_anime="en",
                is_collaborator=False,
            )

        code = (await Users.get(id=callback.from_user.id)).language_bot
    else:
        if len(await Chats.filter(id=chat.id)) == 0:
            await Chats.create(
                id=chat.id,
                title=chat.title,
                username=chat.username or "",
                language="en",
            )

        code = (await Chats.get(id=message.chat.id)).language
    callback._lang = lang.get_language(code)
