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

import base64
import os

import httpx
import pendulum
from pyrogram import filters
from pyrogram.types import InputMediaPhoto, Message
from pyromod.helpers import ikb

from amime.amime import Amime


@Amime.on_message(filters.cmd(r"scan$") & filters.reply)
async def anime_scan(bot: Amime, message: Message):
    reply = message.reply_to_message
    chat = message.chat
    lang = message._lang

    if not reply.media:
        await message.reply_text(lang.media_not_found_text)
        return

    if not (
        bool(reply.photo)
        or bool(reply.sticker)
        or bool(reply.animation)
        or bool(reply.video)
    ):
        await message.reply_text(lang.unsupported_media_format_text)
        return

    media = reply.photo or reply.sticker or reply.animation or reply.video

    sent = await message.reply_photo(
        "https://i.imgur.com/m0N2pFc.jpg", caption=lang.scanning_media_text
    )

    path = await bot.download_media(media)
    file = None
    with open(path, "rb") as f:
        file = base64.b64encode(f.read())
        f.close()

    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(
            "https://trace.moe/api/search", data=dict(image=file), timeout=None
        )
        results = response.json()["docs"]
        if isinstance(results, str) or results is None:
            await sent.edit(lang.no_results_text)
            return

        result = results[0]

        text = f"<b>{result['title_romaji']}</b>"
        if bool(result["title_native"]):
            text += f" (<code>{result['title_native']}</code>)"
        text += "\n"
        at = pendulum.from_timestamp(result["at"]).to_time_string()
        text += f"\n<b>{lang.at}</b>: <code>{at}</code>"
        if bool(result["episode"]):
            text += f"\n<b>{lang.episode}</b>: <code>{result['episode']}</code>"
        percent = round(result["similarity"] * 100, 2)
        text += f"\n<b>{lang.similarity}</b>: <code>{percent}%</code>"

        await sent.edit_media(
            InputMediaPhoto(
                f"https://img.anili.st/media/{result['anilist_id']}",
                text,
            ),
            reply_markup=ikb(
                [
                    [
                        (lang.view_more_button, f"anime {result['anilist_id']}"),
                    ]
                ]
            ),
        )

        await client.aclose()

    os.remove(path)
