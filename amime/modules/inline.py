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

import anilist
import re

from pyrogram import filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
from pyromod.helpers import ikb
from typing import Dict, List

from ..amime import Amime


@Amime.on_inline_query()
async def answer(bot: Amime, inline_query: InlineQuery):
    lang = inline_query._lang
    results: List[InlineQueryResultPhoto] = []
    is_gallery: bool = False

    query = inline_query.query.split()
    if len(query) > 1:
        if query[0].startswith("!"):
            if query[0] in ["!a", "!m"]:
                if query[1].startswith("!"):
                    if query[1] == "!g":
                        is_gallery = True
                    search = " ".join(query[2:])
                else:
                    search = " ".join(query[1:])
                content_type = "anime" if query[0] == "!a" else "manga"

                async with anilist.AsyncClient() as client:
                    results_search = await client.search(search, content_type, 10)
                    for result in results_search:
                        result = await client.get(result.id, content_type)
                        if hasattr(result, "banner"):
                            photo = result.banner
                        elif hasattr(result.cover, "extra_large"):
                            photo = result.cover.extra_large
                        elif hasattr(result.cover, "large"):
                            photo = result.cover.large
                        elif hasattr(result.cover, "medium"):
                            photo = result.cover.medium

                        description = result.description
                        if description:
                            description = re.sub(re.compile(r"<.*?>"), "", description)
                            description = description[0:260] + "..."

                        if is_gallery:
                            text = ""
                        else:
                            text = f"<b>{result.title.romaji}</b> (<code>{result.title.native}</code>)\n"
                            text += f"\n<b>{lang.id}</b>: <code>{result.id}</code> (<b>{content_type.upper()}</b>)"
                            text += f"\n<b>{lang.score}</b>: (<b>{lang.average} = <code>{result.score.average or 0}</code></b>)"
                            text += (
                                f"\n<b>{lang.status}</b>: <code>{result.status}</code>"
                            )
                            text += f"\n<b>{lang.genres}</b>: <code>{', '.join(result.genres)}</code>"
                            if hasattr(result, "studios"):
                                text += f"\n<b>{lang.studios}</b>: <code>{', '.join(result.studios)}</code>"
                            if hasattr(result, "format"):
                                text += f"\n<b>{lang.format}</b>: <code>{result.format}</code>"
                            text += f"\n<b>{lang.start_date}</b>: <code>{result.start_date.day or 0}/{result.start_date.month or 0}/{result.start_date.year or 0}</code>"
                            if not result.status.lower() == "releasing":
                                text += f"\n<b>{lang.end_date}</b>: <code>{result.end_date.day or 0}/{result.end_date.month or 0}/{result.end_date.year or 0}</code>"
                            text += f"\n\n<b>{lang.short_description}</b>: <i>{description}</i>"

                        kwargs: Dict = {}
                        if not is_gallery:
                            keyboard = [
                                [
                                    (
                                        lang.view_more_button,
                                        f"https://t.me/{bot.me.username}?start={content_type}_{result.id}",
                                        "url",
                                    )
                                ]
                            ]
                            kwargs["reply_markup"] = ikb(keyboard)

                        results.append(
                            InlineQueryResultPhoto(
                                photo_url=photo,
                                title=result.title.romaji,
                                description=description,
                                caption=text,
                                **kwargs,
                            )
                        )
    else:
        keyboard = [
            [
                (
                    lang.help_button,
                    f"https://t.me/{bot.me.username}?start=help_inline",
                    "url",
                )
            ]
        ]
        results.append(
            InlineQueryResultArticle(
                title="Usage",
                input_message_content=InputTextMessageContent(
                    lang.inline,
                    parse_mode="html",
                ),
                description="How to use the inline mode",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
                reply_markup=ikb(keyboard),
            )
        )

    if len(results) > 0:
        await inline_query.answer(
            results=results,
            is_gallery=is_gallery,
            cache_time=1,
        )
