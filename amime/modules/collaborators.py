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
from typing import Dict, List, Union

from ..amime import Amime
from ..database import Collaborators, Users


@Amime.on_message(filters.cmd(r"(collabs|collaborators)$") & filters.private)
async def collaborators_message(bot: Amime, message: Message):
    await collaborators_union(bot, message)


@Amime.on_callback_query(filters.regex(r"collaborators"))
async def collaborators_callback(bot: Amime, callback: CallbackQuery):
    await collaborators_union(bot, callback)


async def collaborators_union(bot: Amime, union: Union[CallbackQuery, Message]):
    lang = union._lang
    is_callback = isinstance(union, CallbackQuery)

    text = lang.collaborators(bot_name=bot.me.first_name)

    users = await Users.filter(is_collaborator=True)

    for user in users:
        languages: List[str] = []
        collaborator = await Collaborators.filter(user=user.id)
        for item in collaborator:
            languages.append(item.language)
        username = (
            f"@{user.username}" if len(user.username) > 0 else f"<b>{user.name}</b>"
        )
        text += f"\n    {username} (<i>{', '.join(languages)}</i>)"

    kwargs: Dict = {}
    if is_callback:
        kwargs["reply_markup"] = ikb([[(lang.back_button, "about")]])

    await (union.edit_message_text if is_callback else union.reply_text)(text, **kwargs)
