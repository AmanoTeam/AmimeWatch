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

import anilist
from pyrogram import filters
from pyrogram.types import Message
from pyromod.helpers import ikb

from amime.amime import Amime


@Amime.on_message(filters.cmd(r"character (.+)"))
async def character_view(bot: Amime, message: Message):
    chat = message.chat
    user = message.from_user
    lang = message._lang

    query = message.matches[0].group(2)

    if not bool(query):
        return

    async with anilist.AsyncClient() as client:
        if not query.isdecimal():
            result = (await client.search(query, "character", 1))[0]
            character_id = result.id
        else:
            character_id = int(query)

        character = await client.get(character_id, "character")

        if character is None:
            return

        text = f"<b>{character.name.full}</b>"
        text += f"\n<b>ID</b>: <code>{character.id}</code>"
        if hasattr(character, "favorites"):
            text += f"\n<b>{lang.favorite}s</b>: <code>{character.favorites}</code>"

        text += f"\n\n{character.description}"

        photo: str = ""
        if hasattr(character, "image"):
            if hasattr(character.image, "large"):
                photo = character.image.large
            elif hasatrr(character.image, "medium"):
                photo = character.image.medium

        keyboard = [
            [
                ("🐢 Anilist", character.url, "url"),
            ],
        ]

        if len(text) > 1024:
            text = text[:1021] + "..."

        # Markdown
        text = text.replace("__", "**")
        text = text.replace("~", "~~")

        if len(photo) > 0:
            await message.reply_photo(
                photo,
                caption=text,
                parse_mode="combined",
                reply_markup=ikb(keyboard),
            )
        else:
            await message.reply_text(
                text,
                parse_mode="combined",
                reply_markup=ikb(keyboard),
            )
