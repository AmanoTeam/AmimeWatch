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

import aioanilist

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb
from typing import Union

from ...amime import Amime
from ..favorites import get_favorite_button


@Amime.on_message(filters.cmd(r"manga (?P<id>\d+)") & filters.private)
async def manga_message(bot: Amime, message: Message):
    await view_manga(bot, message)


@Amime.on_callback_query(filters.regex(r"^manga (?P<id>\d+)"))
async def manga_callback(bot: Amime, callback: CallbackQuery):
    await view_manga(bot, callback)


async def view_manga(bot: Amime, union: Union[CallbackQuery, Message]):
    lang = union._lang
    manga_id = int(union.matches[0]["id"])
    is_callback = isinstance(union, CallbackQuery)

    async with aioanilist.Client() as client:
        manga = await client.get("manga", manga_id)

        if manga:
            if manga.description and len(manga.description) > 700:
                manga.description_short = manga.description[0:500] + "..."

            text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"

            text += f"\n<b>{lang.id}</b>: <code>{manga.id}</code>"
            text += f"\n<b>{lang.score}</b>: (<b>{lang.mean} = <code>{manga.score.mean or 0}</code>, {lang.average} = <code>{manga.score.average or 0}</code></b>)"
            text += f"\n<b>{lang.status}</b>: <code>{manga.status}</code>"
            text += f"\n<b>{lang.genres}</b>: <code>{', '.join(manga.genres)}</code>"
            text += f"\n<b>{lang.volume}s</b>: <code>{manga.volumes or 0}</code>"
            text += f"\n<b>{lang.chapter}s</b>: <code>{manga.chapters or 0}</code>"
            text += f"\n<b>{lang.start_date}</b>: <code>{manga.start_date.day or 0}/{manga.start_date.month or 0}/{manga.start_date.year or 0}</code>"
            if not manga.status.lower() == "releasing":
                text += f"\n<b>{lang.end_date}</b>: <code>{manga.end_date.day or 0}/{manga.end_date.month or 0}/{manga.end_date.year or 0}</code>"

            text += "\n"

            if manga.description:
                if hasattr(manga, "description_short"):
                    text += f"\n<b>{lang.short_description}</b>: <i>{manga.description_short}</i>"
                else:
                    text += f"\n<b>{lang.description}</b>: <i>{manga.description}</i>"

            keyboard = [[(lang.read_more_button, manga.url, "url")]]

            keyboard.append(
                [await get_favorite_button(lang, union.from_user, "manga", manga.id)]
            )

            photo = (
                manga.banner
                or manga.cover.extra_large
                or manga.cover.large
                or manga.cover.medium
                or False
            )

            message = union.message if is_callback else union

            if is_callback and message.photo:
                await union.edit_message_text(
                    text,
                    reply_markup=ikb(keyboard),
                )
            else:
                if photo:
                    await message.reply_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=ikb(keyboard),
                    )
                else:
                    await message.reply_text(
                        text=text,
                        reply_markup=ikb(keyboard),
                    )
        else:
            await union.reply_text(
                lang.not_found(type="manga", key="id", value=manga_id)
            )
