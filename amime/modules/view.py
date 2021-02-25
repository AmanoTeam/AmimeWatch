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

import re

from pyrogram import filters
from pyrogram.types import Message

from ..amime import Amime
from .anime.view import view_anime
from .manga.view import view_manga


@Amime.on_message(filters.private & filters.via_bot)
async def view_content(bot: Amime, message: Message):
    lang = message._lang
    from_bot = message.via_bot
    if from_bot.id == bot.me.id and from_bot.username == bot.me.username:
        if message.photo:
            if message.caption:
                text = message.caption
                lines = text.split("\n")
                for line in lines:
                    if len(line) in [0, 1]:
                        continue
                    if lang.id.lower() in line.lower():
                        matches = re.match(
                            lang.id.lower() + r": (\d+) \((\w+)\)", line.lower()
                        )
                        content_id = matches[1]
                        content_type = matches[2]
                        message.matches = [{"id": content_id}]
                        if content_type == "anime":
                            await view_anime(bot, message)
                        elif content_type == "manga":
                            await view_manga(bot, message)
                        break
