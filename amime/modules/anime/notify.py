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

from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import ikb
from typing import Dict

from ...amime import Amime
from ...database import Chats, Notifications, Notify, Users
from .manage import manage_episodes_callback


@Amime.on_callback_query(
    filters.regex(r"notify anime (?P<id>\d+) (?P<language>\w+) (?P<page>\d+)")
)
async def notify_anime_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    language = callback.matches[0]["language"]
    page = int(callback.matches[0]["page"])
    lang = callback._lang

    keyboard = [
        [
            (lang.confirm_button, f"notify anime confirm {anime_id} {language} {page}"),
            (lang.cancel_button, f"manage episodes {anime_id} {page}"),
        ]
    ]

    await callback.edit_message_text(
        lang.confirm,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"notify anime confirm (?P<id>\d+) (?P<language>\w+) (?P<page>\d+)")
)
async def notify_anime_confirm_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    language = callback.matches[0]["language"]
    page = int(callback.matches[0]["page"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime = await anilist.AsyncClient().get(anime_id)

    chats = await Notify.filter(item=anime.id, type="anime")
    episodes = await Notifications.filter(
        item=anime.id, type="anime", language=language
    )

    seasons: Dict = {}
    for episode in episodes:
        if episode.season not in seasons.keys():
            seasons[episode.season] = []
        if episode not in seasons[episode.season]:
            seasons[episode.season].append(episode)

    lang = lang.get_language("en")
    date = episodes[-1].datetime.strftime("%H:%M:%S - %d/%m/%Y")
    text = lang.episode_notification(title=anime.title.romaji, id=anime.id)
    text += f"\n<b>Added</b>:"
    for season, eps in seasons.items():
        text += "\n    "
        if int(season) > 0:
            text += f"<b>S{season}</b>: "
        for ep in eps:
            text += f"E{ep.number} ({ep.language}), "
        text = text[: len(text) - 2]
    text += f"\n\n<b>Date</b>: {date}"
    keyboard = [
        [
            (
                lang.watch_button,
                f"https://t.me/{bot.me.username}?start=anime_{anime.id}",
                "url",
            )
        ]
    ]
    await bot.send_photo(
        chat_id=bot.channel_id,
        photo=f"https://img.anili.st/media/{anime.id}",
        caption=text,
        reply_markup=ikb(keyboard),
    )

    notified_chats = []

    for chat in chats:
        if chat.recipient_type == "group":
            recipient_language = (await Chats.get(id=chat.recipient)).language
        else:
            recipient_language = (await Users.get(id=chat.recipient)).language_bot
        lang = lang.get_language(recipient_language)

        text = lang.episode_notification(title=anime.title.romaji, id=anime.id)
        text += f"\n<b>{lang.added}</b>:"
        for season, eps in seasons.items():
            text += "\n    "
            if int(season) > 0:
                text += f"<b>{lang.season[0]}{season}</b>: "
            for ep in eps:
                text += f"{lang.episode[0]}{ep.number} ({ep.language}), "
            text = text[: len(text) - 2]
        text += f"\n\n<b>{lang.date}</b>: {date}"

        if chat.recipient_type == "group":
            keyboard = [
                [
                    (
                        lang.watch_button,
                        f"https://t.me/{bot.me.username}?start=anime_{anime.id}",
                        "url",
                    )
                ]
            ]
        else:
            keyboard = [[(lang.watch_button, f"anime {anime.id}")]]

        notified_chats.append(
            await bot.send_photo(
                chat_id=chat.recipient,
                photo=f"https://img.anili.st/media/{anime.id}",
                caption=text,
                reply_markup=ikb(keyboard),
            )
        )

    await callback.answer(
        lang.notified_users(count=len(notified_chats)), show_alert=True
    )

    for episode in episodes:
        await episode.delete()

    callback.matches = [{"id": anime.id, "page": page}]
    await manage_episodes_callback(bot, callback)
