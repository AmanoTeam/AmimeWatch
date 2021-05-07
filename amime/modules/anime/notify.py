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

import anilist
from pyrogram import filters
from pyrogram.errors import ChannelInvalid, ChatWriteForbidden, PeerIdInvalid
from pyrogram.types import CallbackQuery
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.config import CHANNELS
from amime.database import Chats, Notifications, Notify, Users
from amime.modules.anime.manage import anime_manage


@Amime.on_callback_query(filters.regex(r"^notify episodes (\d+) (\d+) (\w+) (\d+)"))
async def notify_episodes(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    language = callback.matches[0].group(3)
    page = int(callback.matches[0].group(4))

    keyboard = [
        [
            (
                lang.confirm_button,
                f"notify episodes confirm {anime_id} {season} {language} {page}",
            ),
            (
                lang.cancel_button,
                f"manage anime {anime_id} {season} {language} {page}",
            ),
        ],
    ]

    await message.edit_text(
        lang.confirm_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"^notify episodes confirm (\d+) (\d+) (\w+) (\d+)")
)
async def notify_episodes_confirm(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    language = callback.matches[0].group(3)

    anime = await anilist.AsyncClient().get(anime_id)

    notifications = await Notifications.filter(
        item=anime_id,
        type="anime",
        language=language,
    )
    notifications = sorted(notifications, key=lambda notification: notification.number)

    lang = lang.get_language(language)
    date = notifications[-1].datetime.strftime("%H:%M:%S - %d/%m/%Y")

    text = lang.notify_users_episodes_text(title=anime.title.romaji, id=anime_id)
    text += f"\n<b>{lang.episode}s</b>:"

    seasons = {}
    for notification in notifications:
        if notification.season not in seasons:
            seasons[notification.season] = []

        seasons[notification.season].append(notification.number)

    for season in seasons.values():
        season.sort()

    for season in seasons.items():
        text += "\n    "
        if season[0] > 0:
            text += f"<b>{lang.season[0]}{season[0]}</b>: "
        text += f"<code>{season[1][0]}"
        if len(season[1]) > 1:
            text += f"-{season[1][-1]}"
        text += "</code>"

    text += f"\n\n<b>{lang.date}</b>: {date}"

    keyboard = [
        [
            (
                lang.watch_button,
                f"https://t.me/{bot.me.username}/?start=anime_{anime_id}",
                "url",
            ),
        ]
    ]

    try:
        await bot.send_photo(
            CHANNELS[lang.code],
            f"https://img.anili.st/media/{anime.id}",
            text,
            reply_markup=ikb(keyboard),
        )
    except (ChannelInvalid, ChatWriteForbidden):
        pass

    chats = await Notify.filter(item=anime_id, type="anime")
    for chat in chats:
        l = None
        keyboard = None

        if chat.recipient_type == "user":
            l = (await Users.get(id=chat.recipient)).language_anime

            keyboard = [
                [
                    (lang.watch_button, f"anime {anime_id}"),
                ]
            ]
        else:
            l = (await Chats.get(id=chat.recipient)).language

            keyboard = [
                [
                    (
                        lang.watch_button,
                        f"https://t.me/{bot.me.username}/?start=anime_{anime_id}",
                        "url",
                    ),
                ]
            ]
        if l == language:
            try:
                await bot.send_photo(
                    chat.recipient,
                    f"https://img.anili.st/media/{anime.id}",
                    text,
                    reply_markup=ikb(keyboard),
                )
            except (ChannelInvalid, ChatWriteForbidden, PeerIdInvalid):
                pass

    for notification in notifications:
        await notification.delete()

    lang = callback._lang

    await callback.answer(lang.notified_users_alert, show_alert=True)

    await anime_manage(bot, callback)
