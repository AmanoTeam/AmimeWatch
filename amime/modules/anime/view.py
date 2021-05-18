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
import math
from typing import Union

import anilist
from pyrogram import filters
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.database import Episodes, Users
from amime.modules.favorites import get_favorite_button
from amime.modules.notify import get_notify_button


@Amime.on_message(filters.cmd(r"anime (.+)"))
@Amime.on_callback_query(filters.regex(r"^anime (\d+)\s?(\d+)?\s?(\d+)?"))
async def anime_view(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    chat = message.chat
    user = union.from_user
    lang = union._lang

    is_private = await filters.private(bot, message)
    is_collaborator = await filters.collaborator(bot, union) or await filters.sudo(
        bot, union
    )

    query = union.matches[0].group(1)

    if is_callback:
        user_id = union.matches[0].group(2)
        if user_id is not None:
            user_id = int(user_id)

            if user_id != user.id:
                return

        to_delete = union.matches[0].group(3)
        if bool(to_delete) and not is_private:
            await message.delete()

    if not bool(query):
        return

    async with anilist.AsyncClient() as client:
        if not query.isdecimal():
            results = await client.search(query, "anime", 10)
            if results is None:
                await asyncio.sleep(0.5)
                results = await client.search(query, "anime", 10)

            if results is None:
                return

            if len(results) == 1:
                anime_id = results[0].id
            else:
                keyboard = []
                for result in results:
                    keyboard.append(
                        [(result.title.romaji, f"anime {result.id} {user.id} 1")]
                    )
                await message.reply_text(
                    lang.search_results_text(
                        query=query,
                    ),
                    reply_markup=ikb(keyboard),
                )
                return
        else:
            anime_id = int(query)

        anime = await client.get(anime_id, "anime")

        if anime is None:
            return

        user_db = await Users.get(id=user.id)
        language = user_db.language_anime

        episodes = await Episodes.filter(anime=anime.id)
        episodes = sorted(episodes, key=lambda episode: episode.number)
        episodes = [*filter(lambda episode: len(episode.file_id) > 0, episodes)]

        text = f"<b>{anime.title.romaji}</b>"
        if hasattr(anime.title, "native"):
            text += f" (<code>{anime.title.native}</code>)"
        text += f"\n\n<b>ID</b>: <code>{anime.id}</code>"
        if hasattr(anime, "score"):
            if hasattr(anime.score, "average"):
                text += f"\n<b>{lang.score}</b>: <code>{anime.score.average}</code>"
        text += f"\n<b>{lang.status}</b>: <code>{anime.status}</code>"
        if hasattr(anime, "genres"):
            text += f"\n<b>{lang.genres}</b>: <code>{', '.join(anime.genres)}</code>"
        if hasattr(anime, "studios"):
            text += f"\n<b>{lang.studios}</b>: <code>{', '.join(anime.studios)}</code>"
        text += f"\n<b>{lang.format}</b>: <code>{anime.format}</code>"
        if hasattr(anime, "duration"):
            text += f"\n<b>{lang.duration}</b>: <code>{anime.duration}m</code>"
        if not anime.format.lower() == "movie" and hasattr(anime, "episodes"):
            text += f"\n<b>{lang.episode}s</b>: <code>{anime.episodes}</code>"
        if not anime.status.lower() == "not_yet_released":
            text += f"\n<b>{lang.start_date}</b>: <code>{anime.start_date.day if hasattr(anime.start_date, 'day') else 0}/{anime.start_date.month if hasattr(anime.start_date, 'month') else 0}/{anime.start_date.year if hasattr(anime.start_date, 'year') else 0}</code>"
        if not anime.status.lower() in ["not_yet_released", "releasing"]:
            text += f"\n<b>{lang.end_date}</b>: <code>{anime.end_date.day if hasattr(anime.end_date, 'day') else 0}/{anime.end_date.month if hasattr(anime.end_date, 'month') else 0}/{anime.end_date.year if hasattr(anime.end_date, 'year') else 0}</code>"

        buttons = [
            (lang.view_more_button, f"anime more {anime.id} {user.id}"),
        ]

        if is_private:
            buttons.append(await get_favorite_button(lang, user, "anime", anime.id))

        if len(episodes) > 0:
            if is_private:
                if anime.format.lower() == "movie":
                    buttons.append((lang.watch_button, f"episode {anime.id} 0 1"))
                else:
                    buttons.append(
                        (
                            lang.watch_button,
                            f"episodes {anime.id} {episodes[0].season} 1",
                        )
                    )
            else:
                buttons.append(
                    (
                        lang.watch_button,
                        f"https://t.me/{bot.me.username}/?start=anime_{anime.id}",
                        "url",
                    )
                )

        buttons.append(
            await get_notify_button(
                lang, user if is_private else chat, "anime", anime.id
            )
        )

        if is_private and is_collaborator:
            buttons.append(
                (
                    lang.manage_button,
                    f"manage anime {anime.id} 0 1 {language} 1",
                )
            )

        if is_private and not anime.status.lower() == "not_yet_released":
            button = (
                lang.request_content_button,
                f"request episodes {anime.id} {language}",
            )
            if anime.status.lower() == "releasing":
                if hasattr(anime, "next_airing"):
                    next_episode = anime.next_airing.episode
                    if len(episodes) < (next_episode - 1):
                        buttons.append(button)
                else:
                    buttons.append(button)
            elif hasattr(anime, "episodes"):
                if len(episodes) < anime.episodes:
                    buttons.append(button)

        keyboard = array_chunk(buttons, 2)

        photo = f"https://img.anili.st/media/{anime.id}"

        if bool(message.video) and is_callback:
            await union.edit_message_media(
                InputMediaPhoto(
                    photo,
                    caption=text,
                ),
                reply_markup=ikb(keyboard),
            )
        elif bool(message.photo) and not bool(message.via_bot):
            await message.edit_text(
                text,
                reply_markup=ikb(keyboard),
            )
        else:
            await message.reply_photo(
                photo,
                caption=text,
                reply_markup=ikb(keyboard),
            )


@Amime.on_callback_query(filters.regex(r"^anime more (\d+) (\d+)"))
async def anime_view_more(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        buttons = [
            (lang.description_button, f"anime description {anime_id} {user_id} 1"),
            (lang.characters_button, f"anime characters {anime_id} {user_id}"),
            (lang.studios_button, f"anime studios {anime_id} {user_id}"),
        ]

        if hasattr(anime, "trailer"):
            if hasattr(anime.trailer, "url"):
                buttons.append((lang.trailer_button, anime.trailer.url, "url"))

        buttons.append(("🐢 Anilist", anime.url, "url"))

        keyboard = array_chunk(buttons, 2)

        keyboard.append([(lang.back_button, f"anime {anime_id} {user_id}")])

        await message.edit_text(
            lang.view_more_text,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"anime description (\d+) (\d+) (\d+)"))
async def anime_view_description(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))
    page = int(callback.matches[0].group(3))

    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        description = anime.description
        amount = 1024
        page = 1 if page <= 0 else page
        offset = (page - 1) * amount
        stop = offset + amount
        pages = math.ceil(len(description) / amount)
        description = description[offset - (3 if page > 1 else 0) : stop]

        page_buttons = []
        if page > 1:
            page_buttons.append(
                ("⬅️", f"anime description {anime_id} {user_id} {page - 1}")
            )
        if not page == pages:
            description = description[: len(description) - 3] + "..."
            page_buttons.append(
                ("➡️", f"anime description {anime_id} {user_id} {page + 1}")
            )

        keyboard = []
        if len(page_buttons) > 0:
            keyboard.append(page_buttons)

        keyboard.append([(lang.back_button, f"anime more {anime_id} {user_id}")])

        await message.edit_text(
            description,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"^anime characters (\d+) (\d+)"))
async def anime_view_characters(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        keyboard = [
            [
                (lang.back_button, f"anime more {anime_id} {user_id}"),
            ],
        ]

        text = lang.characters_text

        characters = sorted(anime.characters, key=lambda character: character.id)
        for character in characters:
            text += f"\n• <code>{character.id}</code> - <a href='https://t.me/{bot.me.username}/?start=character_{character.id}'>{character.name.full}</a> (<i>{character.role}</i>)"

        await message.edit_text(
            text,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"^anime studios (\d+) (\d+)"))
async def anime_view_studios(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    if user_id != user.id:
        return

    await callback.answer(lang.unfinished_function_alert, show_alert=True)
