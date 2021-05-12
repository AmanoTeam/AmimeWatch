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

import datetime
import re

import anilist
from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.config import CHATS
from amime.database import Requests
from amime.modules.anime.view import anime_view


@Amime.on_callback_query(filters.regex(r"^request episodes (\d+) (\w+)"))
async def request_episodes(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    language = callback.matches[0].group(2)

    buttons = []
    for code, obj in lang.strings.items():
        text, data = (
            (f"✅ {obj['LANGUAGE_NAME']}", "noop")
            if code == language
            else (
                obj["LANGUAGE_NAME"],
                f"request episodes {anime_id} {code}",
            )
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    keyboard.append(
        [
            (lang.confirm_button, f"request episodes confirm {anime_id} {language}"),
            (lang.back_button, f"anime {anime_id} {user.id}"),
        ]
    )

    await message.edit_text(
        lang.request_content_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^request episodes confirm (\d+) (\w+)"))
async def request_episodes_confirm(bot: Amime, callback: CallbackQuery):
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    language = callback.matches[0].group(2)

    anime = await anilist.AsyncClient().get(anime_id)

    is_collaborator = await filters.collaborator(bot, callback) or bot.is_sudo(user)

    requests = await Requests.filter(item=anime_id, type="anime")
    requests = sorted(requests, key=lambda request: request.id)

    now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

    if not is_collaborator and len(requests) > 0:
        request = requests[-1]
        request_date = request.datetime
        date = now_date - request_date
        if date.seconds < (1 * 60 * 60 * 24):
            await callback.answer(
                lang.requested_in_last_24h_alert(
                    date=request_date.strftime("%H:%M:%S - %d/%m/%Y")
                ),
                show_alert=True,
            )
            return

    await Requests.create(
        user=user.id,
        item=anime_id,
        type="anime",
        datetime=now_date,
        done=False,
    )

    text = "<b>New request</b>"
    text += f"\n<b>From</b>: {user.mention()}"
    text += "\n<b>Anime</b>:"
    text += f"\n    <b>ID</b>: <code>{anime.id}</code>"
    text += f"\n    <b>Name</b>: <code>{anime.title.romaji}</code>"
    text += (
        f"\n    <b>Language</b>: <code>{lang.strings[language]['LANGUAGE_NAME']}</code>"
    )
    text += "\n\n#REQUEST"

    await bot.send_message(
        CHATS["requests"],
        text,
        reply_markup=ikb([[("🆙 Get", f"request get anime {anime_id} {language}")]]),
    )

    await callback.answer(lang.request_sent_alert, show_alert=True)

    matches = re.match(r"(\d+) (\d+)\s?(\d+)?", f"{anime_id} {user.id}")
    callback.matches = [matches]

    await anime_view(bot, callback)
