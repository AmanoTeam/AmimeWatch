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

import re
from typing import Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.modules.anime.view import anime_view
from amime.modules.character.view import character_view
from amime.modules.manga.view import manga_view


@Amime.on_message(filters.cmd(r"start$"))
@Amime.on_callback_query(filters.regex(r"^start$"))
async def start(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    user = union.from_user
    lang = union._lang

    if await filters.private(bot, message):
        await (message.edit_text if is_callback else message.reply_text)(
            lang.start_text_2.format(
                user_mention=user.mention(),
                bot_name=bot.me.first_name,
            ),
            reply_markup=ikb(
                [
                    [
                        (lang.about_button, "about"),
                        (lang.language_button, "language"),
                    ],
                    [
                        (lang.anime_button, "anime"),
                        (lang.manga_button, "manga"),
                    ],
                    [
                        (lang.how_to_use_button, "how_to_use"),
                        (lang.donate_button, "donate"),
                    ],
                ]
            ),
        )
    else:
        await message.reply_text(
            lang.start_text.format(
                user_mention=user.mention(),
                bot_name=bot.me.first_name,
            ),
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


@Amime.on_message(
    filters.cmd(r"start (?P<content_type>anime|character|manga)_(\d+)")
    & filters.private
)
async def view(bot: Amime, message: Message):
    content_type = message.matches[0]["content_type"]

    matches = re.search(r"(\d+)", message.text)
    message.matches = [matches]

    if content_type == "anime":
        await anime_view(bot, message)
    elif content_type == "character":
        await character_view(bot, message)
    else:
        await manga_view(bot, message)
