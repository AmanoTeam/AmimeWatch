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
from ...database import Episodes
from ..favorites import get_favorite_button


@Amime.on_message(filters.cmd(r"anime (?P<id>\d+)"))
async def anime_message(bot: Amime, message: Message):
    await view_anime(bot, message)


@Amime.on_callback_query(filters.regex(r"^anime (?P<id>\d+)"))
async def anime_callback(bot: Amime, callback: CallbackQuery):
    await view_anime(bot, callback)


async def view_anime(bot: Amime, union: Union[CallbackQuery, Message]):
    lang = union._lang
    anime_id = int(union.matches[0]["id"])
    is_callback = isinstance(union, CallbackQuery)
    is_private = await filters.private(bot, union.message if is_callback else union)

    async with aioanilist.Client() as client:
        anime = await client.get("anime", anime_id)

        if anime:
            if anime.description and len(anime.description) > 700:
                anime.description_short = anime.description[0:500] + "..."

            text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

            text += f"\n<b>{lang.id}</b>: <code>{anime.id}</code>"
            text += f"\n<b>{lang.score}</b>: (<b>{lang.mean} = <code>{anime.score.mean or 0}</code>, {lang.average} = <code>{anime.score.average or 0}</code></b>)"
            text += f"\n<b>{lang.status}</b>: <code>{anime.status}</code>"
            text += f"\n<b>{lang.genres}</b>: <code>{', '.join(anime.genres)}</code>"
            if anime.studios.nodes:
                text += f"\n<b>{lang.studios}</b>: <code>{', '.join(studio.name for studio in anime.studios.nodes)}</code>"
            text += f"\n<b>{lang.format}</b>: <code>{anime.format}</code>"
            text += f"\n<b>{lang.duration}</b>: <code>{anime.duration or 24}m</code>"
            episodes = await Episodes.filter(anime=anime.id)
            if not anime.format.lower() == "movie":
                if len(episodes) > 0:
                    text += f"\n<b>{lang.episode}s</b>: (<b>{lang.available_to_watch}: <code>{len(episodes)}/{anime.episodes}</code></b>)"
                else:
                    text += f"\n<b>{lang.episode}s</b>: <code>{anime.episodes}</code>"
            text += f"\n<b>{lang.start_date}</b>: <code>{anime.start_date.day or 0}/{anime.start_date.month or 0}/{anime.start_date.year or 0}</code>"
            if not anime.status.lower() == "releasing":
                text += f"\n<b>{lang.end_date}</b>: <code>{anime.end_date.day or 0}/{anime.end_date.month or 0}/{anime.end_date.year or 0}</code>"

            text += "\n"

            if anime.description:
                if hasattr(anime, "description_short"):
                    text += f"\n<b>{lang.short_description}</b>: <i>{anime.description_short}</i>"
                else:
                    text += f"\n<b>{lang.description}</b>: <i>{anime.description}</i>"

            keyboard = [[(lang.read_more_button, anime.url, "url")]]

            if hasattr(anime.trailer, "url"):
                keyboard[0].append((lang.trailer_button, anime.trailer.url, "url"))

            if is_private:
                keyboard.append(
                    [
                        await get_favorite_button(
                            lang, union.from_user, "anime", anime.id
                        )
                    ]
                )

                if len(episodes) > 0:
                    keyboard[-1].append(
                        (lang.episodes_button, f"episodes {anime.id} 1")
                    )
                    keyboard[-1].sort(reverse=True)

                if await filters.collaborator(bot, union) or await filters.sudo(
                    bot, union
                ):
                    keyboard[-1].append(
                        (lang.manage_button, f"manage anime {anime.id}")
                    )

                if not (
                    await filters.collaborator(bot, union)
                    or await filters.sudo(bot, union)
                ):
                    keyboard.append(
                        [
                            (
                                lang.request_episodes_button,
                                f"request episodes question {anime_id}",
                            )
                        ]
                    )

            photo = f"https://img.anili.st/media/{anime.id}"

            if not is_callback:
                await union.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=ikb(keyboard),
                )
            else:
                if union.message.photo:
                    await union.edit_message_text(
                        text,
                        reply_markup=ikb(keyboard),
                    )
                else:
                    await union.message.reply_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=ikb(keyboard),
                    )
        else:
            await union.reply_text(
                lang.not_found(type="anime", key="id", value=anime_id)
            )
