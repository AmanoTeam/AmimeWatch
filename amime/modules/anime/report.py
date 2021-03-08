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
from pyromod.helpers import array_chunk, ikb
from typing import Dict

from ...amime import Amime
from ...database import Reports
from .watch import watch_callback


REPORTING: Dict = {}


@Amime.on_callback_query(
    filters.regex(
        r"report episode (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def report_episode_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    number = int(callback.matches[0]["number"])
    language = callback.matches[0]["language"]
    user = callback.from_user
    lang = callback._lang

    if str(user.id) not in REPORTING.keys():
        REPORTING[str(user.id)] = {}
    if str(anime_id) not in REPORTING[str(user.id)].keys():
        REPORTING[str(user.id)][str(anime_id)] = {}

    reporting = REPORTING[str(user.id)][str(anime_id)]

    text = lang.report + "\n"

    keyboard = []

    report_types = ["bad_quality", "wrong_episode", "wrong_title", "other"]
    buttons: List[Tuple] = []
    for report_type in report_types:
        name = lang.strings[lang.code][report_type]
        data = f"report type {report_type} {anime_id} {season} {number} {language}"
        buttons.append((name, data))
    keyboard += array_chunk(buttons, 2)

    if "type" in reporting.keys():
        report_type = lang.strings[lang.code][reporting["type"]]
        text += f"\n<b>{lang.type}</b>: <code>{report_type}</code>"

    if "notes" in reporting.keys():
        text += f"\n\n<b>{lang.notes}</b>: <i>{reporting['notes']}</i>"
        keyboard.append(
            [
                (
                    f"✏️ {lang.notes}",
                    f"report add notes {anime_id} {season} {number} {language}",
                )
            ]
        )
    else:
        keyboard.append(
            [
                (
                    f"➕ {lang.notes}",
                    f"report add notes {anime_id} {season} {number} {language}",
                )
            ]
        )

    keyboard.append(
        [
            (
                lang.confirm_button,
                f"report confirm {anime_id} {season} {number} {language}",
            ),
            (
                lang.cancel_button,
                f"report cancel {anime_id} {season} {number} {language}",
            ),
        ]
    )

    await callback.edit_message_text(
        text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(
        r"report type (?P<type>\w+) (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def report_type_callback(bot: Amime, callback: CallbackQuery):
    report_type = callback.matches[0]["type"]
    anime_id = int(callback.matches[0]["id"])
    user = callback.from_user
    lang = callback._lang

    REPORTING[str(user.id)][str(anime_id)]["type"] = report_type

    await report_episode_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(
        r"report add (?P<type>\w+) (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def report_add_callback(bot: Amime, callback: CallbackQuery):
    add_type = callback.matches[0]["type"]
    anime_id = int(callback.matches[0]["id"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    await callback.edit_message_reply_markup({})

    item = lang.strings[lang.code][add_type]

    answer = await chat.ask(lang.send_me_the(item=item.lower()))

    try:
        await answer.delete()
    except:
        pass
    try:
        await answer.request.delete()
    except:
        pass

    REPORTING[str(user.id)][str(anime_id)][add_type] = answer.text

    await report_episode_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(
        r"report confirm (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def report_confirm_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    number = int(callback.matches[0]["number"])
    user = callback.from_user
    lang = callback._lang

    reporting = REPORTING[str(user.id)][str(anime_id)]

    anime = await anilist.AsyncClient().get(anime_id)

    reports = await Reports.filter(item=anime_id, type="anime")

    now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    for report in reports:
        report_date = report.datetime
        date = now_date - report_date
        if date.seconds < (1 * 60 * 60 * 24):
            await callback.answer(
                lang.reported_in_last_24h(
                    date=report_date.strftime("%H:%M:%S - %d/%m/%Y")
                ),
                show_alert=True,
            )
            return

    await Reports.create(
        user=user.id,
        item=anime.id,
        type="anime",
        notes=(reporting["notes"] if "notes" in reporting.keys() else ""),
        datetime=now_date,
    )

    text = "<b>New report</b>"
    text += f"\n<b>From</b>: {user.mention()}"
    text += "\n<b>Anime</b>:"
    text += f"\n    <b>ID</b>: <code>{anime.id}</code>"
    text += f"\n    <b>Name</b>: <code>{anime.title.romaji}</code>"
    if season > 0:
        text += f"\n    <b>Season</b>: <code>{season}</code>"
    text += f"\n    <b>Episode</b>: <code>{number}</code>"
    text += "\n\n<b>Report</b>:"
    report_type = lang.strings[lang.code][reporting["type"]]
    text += f"\n    <b>Type</b>: <code>{report_type}</code>"
    if "notes" in reporting.keys():
        text += f"\n    <b>Notes</b>: <i>{reporting['notes']}</i>"
    text += "\n\n#REPORT #EPISODE"

    await bot.send_message(bot.requests_chat.id, text)

    await callback.answer(lang.episode_successfully_reported, show_alert=True)

    del REPORTING[str(user.id)][str(anime_id)]["type"]

    await watch_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(
        r"report cancel (?P<id>\d+) (?P<season>\d+) (?P<number>\d+) (?P<language>\w+)"
    )
)
async def report_cancel_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    user = callback.from_user
    lang = callback._lang

    del REPORTING[str(user.id)][str(anime_id)]

    await watch_callback(bot, callback)
