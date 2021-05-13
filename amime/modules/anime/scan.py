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
import urllib

import httpx
import pendulum
from pyrogram import filters
from pyrogram.types import Document, InputMediaPhoto, Message, Video
from pyromod.helpers import ikb

from amime.amime import Amime


@Amime.on_message(filters.cmd(r"scan$") & filters.reply)
async def anime_scan(bot: Amime, message: Message):
    reply = message.reply_to_message
    lang = message._lang

    if reply.from_user.id == bot.me.id:
        return

    if not reply.media:
        await message.reply_text(lang.media_not_found_text)
        return

    media = (
        reply.photo or reply.sticker or reply.animation or reply.document or reply.video
    )

    if isinstance(media, (Document, Video)):
        if bool(media.thumbs) and len(media.thumbs) > 0:
            media = media.thumbs[0]
        else:
            return

    sent = await message.reply_photo(
        "https://i.imgur.com/m0N2pFc.jpg", caption=lang.scanning_media_text
    )

    path = await bot.download_media(media)
    file = None
    with open(path, "rb") as f:
        file = base64.b64encode(f.read())
        f.close()

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(
                "https://trace.moe/api/search", data=dict(image=file), timeout=20.0
            )
        except httpx.TimeoutException:
            await sent.edit_text(lang.timed_out_text)
            return

        if response.status_code == 200:
            pass
        elif response.status_code == 429:
            await sent.edit_text(lang.api_overuse_text)
            return
        else:
            await sent.edit_text(lang.api_down_text)
            return

        results = response.json()["docs"]
        if isinstance(results, str) or results is None:
            await sent.edit_text(lang.no_results_text)
            return

        result = results[0]

        at = result["at"]
        to_time = result["to"]
        episode = result["episode"]
        anilist_id = result["anilist_id"]
        file_name = result["filename"]
        from_time = result["from"]
        similarity = result["similarity"]
        token_thumb = result["tokenthumb"]
        title_native = result["title_native"]
        title_romaji = result["title_romaji"]

        text = f"<b>{title_romaji}</b>"
        if bool(title_native):
            text += f" (<code>{title_native}</code>)"
        text += "\n"
        text += f"\n<b>ID</b>: <code>{anilist_id}</code>"
        text += f"\n<b>{lang.at}</b>: <code>{pendulum.from_timestamp(at).to_time_string()}</code>"
        if bool(episode):
            text += f"\n<b>{lang.episode}</b>: <code>{episode}</code>"
        text += (
            f"\n<b>{lang.similarity}</b>: <code>{round(similarity * 100, 2)}%</code>"
        )

        await sent.edit_media(
            InputMediaPhoto(
                f"https://img.anili.st/media/{anilist_id}",
                text,
            ),
            reply_markup=ikb(
                [
                    [
                        (lang.view_more_button, f"anime {anilist_id}"),
                    ]
                ]
            ),
        )
        try:
            await sent.reply_video(
                f"https://media.trace.moe/video/{anilist_id}/{urllib.parse.quote(file_name)}?t={at}&token={token_thumb}&size=l",
                caption=f"<code>{file_name}</code>\n\n<code>{pendulum.from_timestamp(from_time).to_time_string()}</code> - <code>{pendulum.from_timestamp(to_time).to_time_string()}</code>",
            )
        except BaseException:
            pass

        await client.aclose()

    os.remove(path)
