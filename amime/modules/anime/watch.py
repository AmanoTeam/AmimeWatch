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
from ...database import Episodes, Users


@Amime.on_callback_query(
    filters.regex(r"^watch (?P<id>\d+) (?P<number>\d+) (?P<language>\w+)")
)
async def watch_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    number = int(callback.matches[0]["number"])
    language = callback.matches[0]["language"]
    user = callback.from_user
    lang = callback._lang

    anime = await aioanilist.Client().get("anime", anime_id)

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

    user_db = await Users.get(id=user.id)

    episode = await Episodes.get(anime=anime_id, number=number, language=language)
    episodes = await Episodes.filter(anime=anime_id, language=language)

    for index, episode in enumerate(episodes):
        if episode.number == number:
            text += f"\n<b>{lang.episode}</b>: <code>{index + 1}/{len(episodes)}</code>"
            if index == 0:
                text += f" (<b>{lang.first}</b>)"
            elif (index + 1) == len(episodes):
                text += f" (<b>{lang.last}</b>)"
            break
    text += f"\n<b>{lang.duration}</b>: <code>{episode.duration}m</code>"
    text += f"\n<b>{lang.language}</b>: <code>{lang.strings[episode.language]['NAME']}</code>"

    keyboard = []
    media_buttons = []

    previous_number = 0
    for episode in episodes:
        if episode.number < number:
            previous_number = episode.number
    if previous_number != 0:
        media_buttons.append(
            (lang.previous_button, f"watch {anime_id} {previous_number} {language}")
        )
    else:
        media_buttons.append((lang.dot_button, "noop"))

    next_number = 0
    for episode in episodes:
        if episode.number > number:
            next_number = episode.number
            break
    if next_number != 0:
        media_buttons.append(
            (lang.next_button, f"watch {anime_id} {next_number} {language}")
        )
    else:
        media_buttons.append((lang.dot_button, "noop"))

    if len(media_buttons) > 0:
        keyboard.append(media_buttons)

    keyboard.append([(lang.back_button, f"episodes {anime_id} {number // 12 }")])

    await callback.edit_message_media(
        InputMediaVideo(
            episode.file_id,
            caption=text,
        ),
        reply_markup=ikb(keyboard),
    )
