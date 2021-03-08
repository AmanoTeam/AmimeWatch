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
import datetime

from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import ikb

from ...amime import Amime
from ...database import Requests
from .view import view_anime


@Amime.on_callback_query(filters.regex(r"request episodes question (?P<id>\d+)"))
async def request_episodes_question_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    lang = callback._lang

    keyboard = [
        [
            (lang.confirm_button, f"request episodes {anime_id}"),
            (lang.cancel_button, f"anime {anime_id}"),
        ]
    ]

    await callback.edit_message_text(
        lang.confirm,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"request episodes (?P<id>\d+)"))
async def request_episodes_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    user = callback.from_user
    lang = callback._lang

    anime = await anilist.AsyncClient().get(anime_id)

    requests = await Requests.filter(item=anime_id, type="anime")

    now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    for request in requests:
        request_date = request.datetime
        date = now_date - request_date
        if date.seconds < (1 * 60 * 60 * 24):
            await callback.answer(
                lang.episodes_request_in_last_24h(
                    date=request_date.strftime("%H:%M:%S - %d/%m/%Y")
                ),
                show_alert=True,
            )
            return

    await Requests.create(user=user.id, item=anime_id, type="anime", datetime=now_date)

    text = "<b>New episode request</b>"
    text += f"\n<b>From</b>: {user.mention()}"
    text += "\n<b>Anime</b>:"
    text += f"\n    <b>ID</b>: <code>{anime.id}</code>"
    text += f"\n    <b>Name</b>: <code>{anime.title.romaji}</code>"
    text += "\n\n#REQUEST #EPISODE"

    await bot.send_message(bot.requests_chat.id, text)

    await callback.answer(lang.episode_request_successfully_sent, show_alert=True)

    await view_anime(bot, callback)
