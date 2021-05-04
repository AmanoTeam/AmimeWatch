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

from pyrogram import filters
from pyrogram.types import Message

from amime.amime import Amime
from amime.modules.anime.view import anime_view
from amime.modules.character.view import character_view
from amime.modules.manga.view import manga_view


@Amime.on_message(filters.private & filters.via_bot)
async def view(bot: Amime, message: Message):
    from_bot = message.via_bot

    if from_bot.id == bot.me.id:
        if bool(message.photo) and bool(message.caption):
            text = message.caption
            lines = text.splitlines()

            for line in lines:
                if "ID" in line:
                    matches = re.match(r"ID: (\d+) \((\w+)\)", line)
                    content_type = matches.group(2).lower()
                    message.matches = [matches]
                    if content_type == "anime":
                        await anime_view(bot, message)
                    elif content_type == "character":
                        await character_view(bot, message)
                    elif content_type == "manga":
                        await manga_view(bot, message)
                    break
