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
from typing import Dict

import anilist
from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.config import CHATS
from amime.database import Reports, Users
from amime.modules.anime.watch import anime_episode

# fmt: off
REPORT_TYPES = [
    "bad_quality", "wrong_episode",
    "wrong_title", "other",
]
# fmt: on

REPORTING: Dict = {}


@Amime.on_callback_query(filters.regex(r"^report episode (\d+) (\d+) (\d+) (\-?\d+)"))
async def report_episode(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    number = int(callback.matches[0].group(3))
    report_type = int(callback.matches[0].group(4))

    if str(user.id) not in REPORTING.keys():
        REPORTING[str(user.id)] = {}
    if str(anime_id) not in REPORTING[str(user.id)].keys():
        REPORTING[str(user.id)][str(anime_id)] = {}

    reporting = REPORTING[str(user.id)][str(anime_id)]

    buttons = []
    for index, r_type in enumerate(REPORT_TYPES):
        text = ("✅ " if index == report_type else "") + lang.strings[lang.code][r_type]
        data = f"report episode {anime_id} {season} {number} {index}"
        buttons.append((text, data))

    text = lang.report_text + "\n"

    if report_type != -1:
        text += f"\n<b>{lang.type}</b>: {lang.strings[lang.code][REPORT_TYPES[report_type]]}"

    if "notes" in reporting.keys():
        text += f"\n\n<b>{lang.notes}</b>: <i>{reporting['notes']}</i>"
        buttons.append(
            (
                f"🗑️ {lang.notes}",
                f"report episode edit notes {anime_id} {season} {number} {report_type}",
            )
        )
    else:
        buttons.append(
            (
                f"➕ {lang.notes}",
                f"report episode edit notes {anime_id} {season} {number} {report_type}",
            )
        )

    keyboard = array_chunk(buttons, 2)

    buttons = []

    if (report_type == 3 and "notes" in reporting.keys()) or (
        report_type > -1 and report_type < 3
    ):
        buttons.append(
            (
                lang.confirm_button,
                f"report episode confirm {anime_id} {season} {number} {report_type}",
            )
        )

    buttons.append((lang.back_button, f"episode {anime_id} {season} {number}"))

    keyboard += array_chunk(buttons, 2)

    await message.edit_text(
        text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"^report episode edit notes (\d+) (\d+) (\d+) (\-?\d+)")
)
async def report_episode_edit_notes(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    number = int(callback.matches[0].group(3))
    report_type = int(callback.matches[0].group(4))

    reporting = REPORTING[str(user.id)][str(anime_id)]

    if "notes" in reporting.keys():
        del reporting["notes"]
    else:
        keyboard = [
            [
                (
                    lang.cancel_button,
                    f"report episode {anime_id} {season} {number} {report_type}",
                ),
            ],
        ]

        await message.edit_text(
            lang.send_me_the_item_text(item=lang.notes.lower()),
            reply_markup=ikb(keyboard),
        )

        answer = await chat.listen(filters.text)
        reporting["notes"] = answer.text

        try:
            await answer.delete()
        except BaseException:
            pass

    REPORTING[str(user.id)][str(anime_id)] = reporting

    await report_episode(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"^report episode confirm (\d+) (\d+) (\d+) (\-?\d+)")
)
async def report_episode_confirm(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    number = int(callback.matches[0].group(3))
    report_type = int(callback.matches[0].group(4))

    reporting = REPORTING[str(user.id)][str(anime_id)]

    anime = await anilist.AsyncClient().get(anime_id)

    user_db = await Users.get(id=user.id)
    language = user_db.language_anime

    is_collaborator = await filters.collaborator(bot, callback) or bot.is_sudo(user)

    reports = await Reports.filter(item=anime_id, type="anime")
    reports = sorted(reports, key=lambda report: report.id)

    now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

    if not is_collaborator and len(reports) > 0:
        report = reports[-1]
        report_date = report.datetime
        date = now_date - report_date
        if date.seconds < (1 * 60 * 60 * 24):
            await callback.answer(
                lang.reported_in_last_24h_alert(
                    date=report_date.strftime("%H:%M:%S - %d/%m/%Y")
                ),
                show_alert=True,
            )
            return

    await Reports.create(
        user=user.id,
        item=anime_id,
        type="anime",
        notes=(reporting["notes"] if "notes" in reporting.keys() else ""),
        datetime=now_date,
    )

    text = "<b>New report</b>"
    text += f"\n<b>From</b>: {user.mention()}"
    text += "\n<b>Anime</b>:"
    text += f"\n    <b>ID</b>: <code>{anime.id}</code>"
    text += f"\n    <b>Name</b>: <code>{anime.title.romaji}</code>"
    if not anime.format.lower() == "movie":
        if season > 0:
            text += f"\n    <b>Season</b>: <code>{season}</code>"
        text += f"\n    <b>Episode</b>: <code>{number}</code>"
    text += (
        f"\n    <b>Language</b>: <code>{lang.strings[language]['LANGUAGE_NAME']}</code>"
    )

    text += "\n\n<b>Report</b>:"
    text += f"\n    <b>Type</b>: <code>{lang.strings['en'][REPORT_TYPES[report_type]]}</code>"
    if "notes" in reporting.keys():
        text += f"\n    <b>Notes</b>: <i>{reporting['notes']}</i>"
    text += "\n\n#REPORT #EPISODE"

    await bot.send_message(CHATS["requests"], text)

    await callback.answer(lang.episode_successfully_reported_alert, show_alert=True)

    del REPORTING[str(user.id)][str(anime_id)]

    await anime_episode(bot, callback)
