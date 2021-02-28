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

from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import array_chunk, ikb
from pyromod.nav import Pagination
from typing import Dict

from ...amime import Amime
from ...database import Episodes, Users, Viewed, Watched


@Amime.on_callback_query(filters.regex(r"episodes (?P<id>\d+) (?P<page>\d+)"))
async def episodes_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    keyboard = [
        [
            (lang.language_button, f"episodes lang {anime_id} {page}"),
        ]
    ]

    user_db = await Users.get(id=user.id)

    episodes = await Episodes.filter(anime=anime_id, language=user_db.language_anime)

    episodes_dict: Dict = {}
    for episode in episodes:
        viewed = (
            len(await Viewed.filter(user=user.id, item=episode.id, type="anime")) > 0
        )
        watched = len(await Watched.filter(user=user.id, episode=episode.id)) > 0
        episodes_dict[episode.id] = [episode, viewed, watched]

    def item_title(i, pg) -> str:
        status = "✅" if i[1][2] else "👁️" if i[1][1] else "🙈"
        return f"{status} {i[1][0].number}"

    layout = Pagination(
        [*episodes_dict.items()],
        item_data=lambda i, pg: f"watch {i[1][0].anime} {i[1][0].number}",
        item_title=item_title,
        page_data=lambda pg: f"episodes {anime_id} {pg}",
    )

    lines = layout.create(page, lines=8, columns=2)

    if len(lines) > 0:
        keyboard += lines
    elif page > 1:
        callback.matches = [{"id": anime_id, "page": page - 1}]
        await episodes_callback(bot, callback)
        return

    keyboard.append([(lang.back_button, f"anime {anime_id}")])

    await callback.edit_message_text(
        lang.episodes(
            count=len(episodes), language=lang.strings[user_db.language_anime]["NAME"]
        ),
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^episodes lang (?P<id>\d+) (?P<page>\d+)"))
async def episodes_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    user_db = await Users.get(id=user.id)

    codes = []
    for episode in await Episodes.filter(anime=anime_id):
        code = episode.language
        if code not in codes:
            codes.append(code)

    buttons: List[Tuple] = []
    for code in codes:
        using = code == user_db.language_anime
        language = lang.strings[code]
        text = ("✅ " if using else "") + language["NAME"]
        data = "noop" if using else f"episodes set lang {anime_id} {page} {code}"
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)
    keyboard.append([(lang.back_button, f"episodes {anime_id} {page}")])

    await callback.edit_message_text(lang.settings_language, reply_markup=ikb(keyboard))


@Amime.on_callback_query(
    filters.regex(r"^episodes set lang (?P<id>\d+) (?P<page>\d+) (?P<code>\w+)")
)
async def episodes_set_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    code = callback.matches[0]["code"]
    user = callback.from_user

    user_db = await Users.get(id=user.id)
    user_db.update_from_dict({"language_anime": code})
    await user_db.save()

    await episodes_lang_callback(bot, callback)
