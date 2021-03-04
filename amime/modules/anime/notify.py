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
from pyrogram.types import CallbackQuery
from typing import Dict

from ...amime import Amime
from ...database import Chats, Notifications, Notify, Users


@Amime.on_callback_query(filters.regex(r"notify anime (?P<id>\d+) (?P<language>\w+)"))
async def notify_anime_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    language = callback.matches[0]["language"]
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime = await aioanilist.Client().get("anime", anime_id)

    chats = await Notify.filter(item=anime.id, type="anime", language=language)
    episodes = await Notifications.filter(
        item=anime.id, type="anime", language=language
    )

    seasons: Dict = {}
    for episode in episodes:
        if str(episode.season) not in seasons.keys():
            seasons[str(episode.season)] = []
        if str(episode.number) not in seasons[str(episode.season)]:
            seasons[str(episode.season)].append(str(episode.number))

    for chat in chats:
        language = chat.language
        lang = lang.get_language(language)

        date = episodes[-1].datetime.strftime("%H:%M:%S - %d/%m/%Y")

        text = lang.episode_notification(name=anime.title.romaji, id=anime.id)
        for season, eps in seasons.items():
            if int(season) > 0:
                text += f"\n    <b>{lang.season[0]}{season}</b>: {lang.episode[0]}<code>{', '.join(eps)}</code>"
            else:
                text += f"\n    {lang.episode[0]}<code>{', '.join(eps)}</code>"
        text += f"\n\n<b>{lang.date}</b>: {date}"

        await bot.send_photo(
            chat_id=chat.recipient,
            photo=f"https://img.anili.st/media/{anime.id}",
            caption=text,
        )

    for episode in episodes:
        await episode.delete()
