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
import math

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import array_chunk, ikb
from typing import Union

from ...amime import Amime
from ...database import Chats, Episodes, Notify, Users
from ..favorites import get_favorite_button


@Amime.on_message(filters.cmd(r"anime (?P<query>.+)"))
async def anime_message(bot: Amime, message: Message):
    query = message.matches[0]["query"]

    if query.isdecimal():
        anime_id = int(query)
    else:
        async with anilist.AsyncClient() as client:
            try:
                result = (await client.search(query, limit=1))[0]
            except:
                return
            anime_id = result.id

    message.matches = [{"id": anime_id}]
    await view_anime(bot, message)


@Amime.on_callback_query(filters.regex(r"^anime (?P<id>\d+)"))
async def anime_callback(bot: Amime, callback: CallbackQuery):
    await view_anime(bot, callback)


async def view_anime(bot: Amime, union: Union[CallbackQuery, Message]):
    anime_id = int(union.matches[0]["id"])
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    is_private = await filters.private(bot, message)
    chat = message.chat
    user = union.from_user
    lang = union._lang

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id)

        if anime:
            text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

            text += f"\n<b>{lang.id}</b>: <code>{anime.id}</code>"
            if hasattr(anime, "score"):
                if hasattr(anime.score, "average"):
                    text += f"\n<b>{lang.score}</b>: (<b>{lang.average} = <code>{anime.score.average}</code></b>)"
            text += f"\n<b>{lang.status}</b>: <code>{anime.status}</code>"
            if hasattr(anime, "genres"):
                text += (
                    f"\n<b>{lang.genres}</b>: <code>{', '.join(anime.genres)}</code>"
                )
            if hasattr(anime, "studios"):
                text += (
                    f"\n<b>{lang.studios}</b>: <code>{', '.join(anime.studios)}</code>"
                )
            text += f"\n<b>{lang.format}</b>: <code>{anime.format}</code>"
            if hasattr(anime, "duration"):
                text += f"\n<b>{lang.duration}</b>: <code>{anime.duration}m</code>"
            if not anime.format.lower() == "movie" and hasattr(anime, "episodes"):
                text += f"\n<b>{lang.episode}s</b>: <code>{anime.episodes}</code>"

            keyboard = [(lang.read_more_button, f"anime more {anime.id}")]

            if is_private:
                keyboard.append(
                    await get_favorite_button(lang, union.from_user, "anime", anime.id)
                )

                episodes = await Episodes.filter(anime=anime.id)
                episodes = sorted(episodes, key=lambda episode: episode.number)

                if len(episodes) > 0:
                    if hasattr(anime, "format") and anime.format.lower() == "movie":
                        keyboard.append((lang.watch_button, f"movie {anime.id}"))
                    else:
                        season = episodes[0].season
                        keyboard.append(
                            (lang.watch_button, f"episodes {anime.id} {season} 1")
                        )

                if not (await filters.collaborator(bot, union) or bot.is_sudo(user)):
                    keyboard.append(
                        (
                            lang.request_episodes_button,
                            f"request episodes question {anime_id}",
                        )
                    )

            if not anime.format.lower() == "movie":
                recipient = user.id if is_private else chat.id
                recipient_type = "user" if is_private else "group"
                notify = await Notify.filter(
                    recipient=recipient,
                    recipient_type=recipient_type,
                    item=anime.id,
                    type="anime",
                )
                if len(notify) > 0:
                    keyboard.append(
                        (
                            f"🔕 {lang.notify_episodes}",
                            f"notify chat {anime.id} {recipient} {recipient_type}",
                        )
                    )
                else:
                    keyboard.append(
                        (
                            f"🔔 {lang.notify_episodes}",
                            f"notify chat {anime.id} {recipient} {recipient_type}",
                        )
                    )

            if is_private:
                if await filters.collaborator(bot, union) or bot.is_sudo(user):
                    keyboard.append((lang.manage_button, f"manage anime {anime.id}"))

            photo = f"https://img.anili.st/media/{anime.id}"

            keyboard = array_chunk(keyboard, 2)

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


@Amime.on_callback_query(filters.regex(r"anime more (?P<id>\d+)"))
async def view_anime_more_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    if not (
        (
            await filters.group(bot, message)
            and await filters.administrator(bot, callback)
        )
        or await filters.private(bot, message)
    ):
        return

    keyboard = [
        [
            (lang.description_button, f"anime description {anime_id} 1"),
            (lang.characters_button, f"anime characters {anime_id}"),
        ],
        [(lang.studios_button, f"anime studios {anime_id}")],
    ]

    keyboard.append([(lang.back_button, f"anime {anime_id}")])

    await callback.edit_message_text(
        lang.anime_more,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"anime description (?P<id>\d+) (?P<page>\d+)"))
async def view_anime_description_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    message = callback.message
    lang = callback._lang

    if not (
        (
            await filters.group(bot, message)
            and await filters.administrator(bot, callback)
        )
        or await filters.private(bot, message)
    ):
        return

    anime = await anilist.AsyncClient().get(anime_id)

    description = anime.description
    amount = 1024
    page = 1 if page <= 0 else page
    offset = (page - 1) * amount
    stop = offset + amount
    pages = math.ceil(len(description) / amount)
    description = description[offset - (3 if page > 1 else 0) : stop]

    keyboard = []

    page_buttons = []
    if page > 1:
        page_buttons.append(("⬅️", f"anime description {anime_id} {page - 1}"))
    if not page == pages:
        description = description[: len(description) - 3] + "..."
        page_buttons.append(("➡️", f"anime description {anime_id} {page + 1}"))

    if len(page_buttons) > 0:
        keyboard.append(page_buttons)

    keyboard.append([(lang.back_button, f"anime more {anime_id}")])

    await callback.edit_message_text(
        description,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"anime characters (?P<id>\d+)"))
async def view_anime_characters_callback(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    if not (
        (
            await filters.group(bot, message)
            and await filters.administrator(bot, callback)
        )
        or await filters.private(bot, message)
    ):
        return

    await callback.answer(lang.function_in_progress, show_alert=True)


@Amime.on_callback_query(filters.regex(r"anime studios (?P<id>\d+)"))
async def view_anime_studios_callback(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    if not (
        (
            await filters.group(bot, message)
            and await filters.administrator(bot, callback)
        )
        or await filters.private(bot, message)
    ):
        return

    await callback.answer(lang.function_in_progress, show_alert=True)


@Amime.on_callback_query(
    filters.regex(
        r"^notify chat (?P<id>\d+) (?P<recipient>(\-)?\d+) (?P<recipient_type>group|user)"
    )
)
async def notify_chat_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    recipient = int(callback.matches[0]["recipient"])
    recipient_type = callback.matches[0]["recipient_type"]
    lang = callback._lang

    if recipient_type == "group":
        if not await filters.administrator(bot, callback):
            return

    notify = await Notify.filter(
        recipient=recipient,
        recipient_type=recipient_type,
        item=anime_id,
        type="anime",
    )
    if len(notify) > 0:
        notify = notify[0]
        await notify.delete()
        await callback.answer(lang.episode_notifications_off, show_alert=True)
    else:
        await Notify.create(
            recipient=recipient,
            recipient_type=recipient_type,
            item=anime_id,
            type="anime",
        )
        await callback.answer(lang.episode_notifications_on, show_alert=True)

    await view_anime(bot, callback)
