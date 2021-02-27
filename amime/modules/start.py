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
from ..database import Users
from .help import help_module_union


@Amime.on_message(filters.cmd(r"start$") & filters.private)
async def start_message(bot: Amime, message: Message):
    await start_union(bot, message)


@Amime.on_callback_query(filters.regex(r"^start$"))
async def start_callback(bot: Amime, callback: CallbackQuery):
    await start_union(bot, callback)


async def start_union(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    lang = union._lang

    keyboard = [[(lang.help_button, "help"), (lang.about_button, "about")]]
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

    if len(await Users.filter(id=user.id)) < 1:
        await Users.create(
            id=user.id,
            name=user.first_name,
            username=user.username or "",
            language_bot=user.language_code or "en-US",
            language_anime=user.language_code or "en-US",
            is_collaborator=False,
        )


@Amime.on_message(filters.cmd(r"start help_(?P<module>.+)") & filters.private)
async def start_help_message(bot: Amime, message: Message):
    await help_module_union(bot, message)
