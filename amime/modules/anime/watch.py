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
from pyrogram.types import CallbackQuery, InputMediaVideo
from pyromod.helpers import ikb

from ...amime import Amime
from ...database import Episodes, Users, Viewed, Watched


@Amime.on_callback_query(
    filters.regex(
        r"^watch (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def watch_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    number = int(callback.matches[0]["number"])
    language = callback.matches[0]["language"]
    user = callback.from_user
    lang = callback._lang

    anime = await aioanilist.Client().get("anime", anime_id)

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

    user_db = await Users.get(id=user.id)

    episode = await Episodes.get(
        anime=anime_id, season=season, number=number, language=language
    )
    episodes = await Episodes.filter(anime=anime_id, season=season, language=language)
    episodes = sorted(episodes, key=lambda ep: ep.number)
    all_episodes = await Episodes.filter(anime=anime_id, language=language)
    all_episodes = sorted(all_episodes, key=lambda episode: episode.number)

    if len(await Viewed.filter(user=user.id, item=episode.id, type="anime")) < 1:
        await Viewed.create(user=user.id, item=episode.id, type="anime")

    if len(episode.name) > 0:
        text += f"\n<b>{lang.name}</b>: <code>{episode.name}</code>"

    if season > 0:
        text += f"\n<b>{lang.season}</b>: <code>{episode.season}</code>"
    text += f"\n<b>{lang.episode}</b>: <code>{episode.number}</code>"
    text += f"\n<b>{lang.duration}</b>: <code>{episode.duration}m</code>"
    text += f"\n<b>{lang.language}</b>: <code>{lang.strings[episode.language]['NAME']}</code>"

    if len(episode.added_by) > 0:
        text += f"\n<b>{lang.added_by}</b>: <b>{episode.added_by}</b>"

    if len(episode.notes) > 0:
        text += f"\n\n<b>{lang.notes}</b>: <i>{episode.notes}</i>"

    keyboard = [
        [
            (
                (
                    lang.mark_as_unwatched_button
                    if len(await Watched.filter(user=user.id, episode=episode.id)) > 0
                    else lang.mark_as_watched_button
                ),
                f"watched {anime_id} {season} {number} {language}",
            )
        ]
    ]

    media_buttons = []
    previous_number = 0
    for ep in episodes:
        if ep.number < number:
            previous_number = ep.number
    if previous_number != 0:
        media_buttons.append(
            (
                lang.previous_button,
                f"watch {anime_id} {season} {previous_number} {language}",
            )
        )
    else:
        previous_season = 0
        seasons = []
        for ep in all_episodes:
            if ep.season not in seasons:
                seasons.append(ep.season)
        for s in seasons:
            eps = await Episodes.filter(anime=anime_id, season=s, language=language)
            eps = sorted(eps, key=lambda episode: episode.number, reverse=True)
            for ep in eps:
                if ep.season < season:
                    previous_season = ep.season
                    previous_number = ep.number
                    break
        if season > 0 and previous_season != 0:
            media_buttons.append(
                (
                    lang.previous_button,
                    f"watch {anime_id} {previous_season} {previous_number} {language}",
                )
            )
        else:
            media_buttons.append((lang.dot_button, "noop"))

    next_number = 0
    for ep in episodes:
        if ep.number > number:
            next_number = ep.number
            break
    if next_number != 0:
        media_buttons.append(
            (lang.next_button, f"watch {anime_id} {season} {next_number} {language}")
        )
    else:
        next_season = 0
        for ep in all_episodes:
            if ep.season > season:
                next_season = ep.season
                next_number = ep.number
                break
        if season > 0 and next_season != 0:
            media_buttons.append(
                (
                    lang.next_button,
                    f"watch {anime_id} {next_season} {next_number} {language}",
                )
            )
        else:
            media_buttons.append((lang.dot_button, "noop"))

    if len(media_buttons) > 0:
        if not (
            media_buttons[0][0] == lang.dot_button
            and media_buttons[1][0] == lang.dot_button
        ):
            keyboard.append(media_buttons)

    keyboard.append(
        [
            (
                lang.report_button,
                f"report episode {anime_id} {season} {number} {language}",
            )
        ]
    )

    keyboard.append(
        [(lang.back_button, f"episodes {anime_id} {season} {number // 12}")]
    )

    await callback.edit_message_media(
        InputMediaVideo(
            episode.file_id,
            caption=text,
        ),
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(
        r"^watched (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def watched_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    number = int(callback.matches[0]["number"])
    language = callback.matches[0]["language"]
    user = callback.from_user
    lang = callback._lang

    episode = await Episodes.get(
        anime=anime_id, season=season, number=number, language=language
    )

    watched = await Watched.filter(user=user.id, episode=episode.id)
    if len(watched) > 0:
        watched = watched[0]
        await watched.delete()
    else:
        await Watched.create(user=user.id, episode=episode.id)

    await watch_callback(bot, callback)
