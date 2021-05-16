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

import asyncio
import re
from typing import List

import anilist
from pyrogram import filters
from pyrogram.types import InlineQuery, InlineQueryResultPhoto
from pyromod.helpers import ikb

from amime.amime import Amime


@Amime.on_inline_query(filters.regex(r"^!m (?P<query>.+)"))
async def manga_inline(bot: Amime, inline_query: InlineQuery):
    query = inline_query.matches[0]["query"].strip()
    lang = inline_query._lang

    results: List[InlineQueryResultPhoto] = []

    async with anilist.AsyncClient() as client:
        search_results = await client.search(query, "manga", 10)
        while search_results is None:
            search_results = await client.search(query, "manga", 10)
            await asyncio.sleep(5)

        for result in search_results:
            manga = await client.get(result.id, "manga")

            if manga is None:
                continue

            photo: str = ""
            if hasattr(manga, "banner"):
                photo = manga.banner
            elif hasattr(manga, "cover"):
                if hasattr(manga.cover, "extra_large"):
                    photo = manga.cover.extra_large
                elif hasattr(manga.cover, "large"):
                    photo = manga.cover.large
                elif hasattr(manga.cover, "medium"):
                    photo = manga.cover.medium

            description: str = ""
            if hasattr(manga, "description"):
                description = manga.description
                description = re.sub(re.compile(r"<.*?>"), "", description)
                description = description[0:260] + "..."

            text = f"<b>{manga.title.romaji}</b>"
            if hasattr(manga.title, "native"):
                text += f" (<code>{manga.title.native}</code>)"
            text += f"\n\n<b>ID</b>: <code>{manga.id}</code> (<b>MANGA</b>)"
            if hasattr(manga, "score"):
                if hasattr(manga.score, "average"):
                    text += f"\n<b>{lang.score}</b>: <code>{manga.score.average}</code>"
            text += f"\n<b>{lang.status}</b>: <code>{manga.status}</code>"
            if hasattr(manga, "genres"):
                text += (
                    f"\n<b>{lang.genres}</b>: <code>{', '.join(manga.genres)}</code>"
                )
            if not manga.status.lower() == "not_yet_released":
                text += f"\n<b>{lang.start_date}</b>: <code>{manga.start_date.day if hasattr(manga.start_date, 'day') else 0}/{manga.start_date.month if hasattr(manga.start_date, 'month') else 0}/{manga.start_date.year if hasattr(manga.start_date, 'year') else 0}</code>"
            if not manga.status.lower() in ["not_yet_released", "releasing"]:
                text += f"\n<b>{lang.end_date}</b>: <code>{manga.end_date.day if hasattr(manga.end_date, 'day') else 0}/{manga.end_date.month if hasattr(manga.end_date, 'month') else 0}/{manga.end_date.year if hasattr(manga.end_date, 'year') else 0}</code>"

            text += f"\n\n<b>{lang.short_description}</b>: <i>{description}</i>"

            keyboard = [
                [
                    (
                        lang.view_more_button,
                        f"https://t.me/{bot.me.username}/?start=manga_{manga.id}",
                        "url",
                    )
                ],
            ]

            results.append(
                InlineQueryResultPhoto(
                    photo_url=photo,
                    title=manga.title.romaji,
                    description=description,
                    caption=text,
                    reply_markup=ikb(keyboard),
                )
            )

    if len(results) > 0:
        await inline_query.answer(
            results=results,
            is_gallery=False,
            cache_time=3,
        )
