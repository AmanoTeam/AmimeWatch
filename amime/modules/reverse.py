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

import os
import re
import urllib

import bs4
import httpx
from pyrogram import filters
from pyrogram.types import Document, InputMediaPhoto, Message, Video

from amime.amime import Amime


@Amime.on_message(filters.cmd(r"reverse$") & filters.reply)
async def reverse(bot: Amime, message: Message):
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
        "https://i.imgur.com/m0N2pFc.jpg", caption=lang.searching_media_text
    )

    path = await bot.download_media(media)

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(
                "https://www.google.com/searchbyimage/upload",
                files=dict(
                    encoded_image=(os.path.basename(path), open(path, "rb")),
                    image_content="",
                ),
                timeout=20.0,
                allow_redirects=False,
            )
        except httpx.TimeoutException:
            await sent.edit_text(lang.timed_out_text)
            return

        if response.status_code == 400:
            await sent.edit_text(lang.api_overuse_text)
            return

        url = response.headers["Location"]

        opener = urllib.request.build_opener()

        source = opener.open(f"{url}&hl=en").read()
        soup = bs4.BeautifulSoup(source, "html.parser")

        results = {
            "similar_images": None,
            "override": None,
            "best_guess": None,
        }

        try:
            for bess in soup.findAll("a", {"class": "PBorbe"}):
                results["override"] = f"https://www.google.com{bess['href']}"
        except BaseException:
            pass

        for similar_image in soup.findAll("input", {"clas": "gLFyf"}):
            results[
                "similar_images"
            ] = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote_plus(similar_image['value'])}"

        for best_guess in soup.findAll("div", {"class": "r5a77d"}):
            results["best_guess"] = best_guess.get_text()

        guess = results["best_guess"]

        page_url = None
        if results["override"] is not None:
            page_url = results["override"]
        else:
            page_url = results["similar_images"]

        if guess is None and page_url is None:
            await sent.edit_text(lang.no_results_text)
            return

        single = opener.open(page_url).read().decode()

        images = []
        count = 0
        for image in re.findall(
            r"^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$", single, re.I | re.M
        ):
            count += 1
            images.append(image)
            if count >= 5:
                break

        if len(images) == 0:
            await sent.edit_text(lang.no_results_text)
            return

        await sent.reply_media_group(media=[InputMediaPhoto(image) for image in images])
        await sent.edit_text(
            lang.search_results_text.format(query=f"<a href='{url}'>{guess}</a>"),
            disable_web_page_preview=True,
        )

        await client.aclose()

    os.remove(path)
