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
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import array_chunk, ikb
from pyromod.nav import Pagination
from typing import Dict, List, Tuple

from ...amime import Amime
from ...database import Collaborators, Episodes


LANGUAGE: Dict = {}


@Amime.on_callback_query(filters.regex(r"^manage anime (?P<id>\d+)"))
async def manage_anime_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    user = callback.from_user
    lang = callback._lang

    language = (
        "en"
        if await filters.sudo(bot, callback)
        else (await Collaborators.filter(user=user.id))[-1].language
    )
    LANGUAGE[str(user.id)] = {f"{anime_id}": language}

    keyboard = [
        [(lang.episodes_button, f"manage episodes {anime_id} 1")],
        [(lang.back_button, f"anime {anime_id}")],
    ]

    await callback.edit_message_text(
        lang.manage_anime,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^manage episodes (?P<id>\d+) (?P<page>\d+)"))
async def manage_episodes_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    keyboard = [
        [
            (lang.add_button, f"manage add episode {anime_id} {page}"),
            (lang.language_button, f"manage lang {anime_id} {page}"),
        ]
    ]

    episodes = await Episodes.filter(
        anime=anime_id, language=LANGUAGE[str(user.id)][str(anime_id)]
    )

    episodes_dict: Dict = {}
    for episode in episodes:
        episodes_dict[episode.id] = episode

    def item_title(i, pg) -> str:
        return f"🗑️ {i[1].number}"

    layout = Pagination(
        [*episodes_dict.items()],
        item_data=lambda i, pg: f"manage del {i[1].anime} {i[1].number} {pg}",
        item_title=item_title,
        page_data=lambda pg: f"manage episodes {anime_id} {pg}",
    )

    lines = layout.create(page, lines=8, columns=2)

    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, f"manage anime {anime_id}")])

    await callback.edit_message_text(
        lang.manage_episodes,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^manage lang (?P<id>\d+) (?P<page>\d+)"))
async def manage_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    codes = (
        list(lang.strings.keys())
        if await filters.sudo(bot, callback)
        else [
            collab_db.language for collab_db in await Collaborators.filter(user=user.id)
        ]
    )

    buttons: List[Tuple] = []
    for code in codes:
        using = code == LANGUAGE[str(user.id)][str(anime_id)]
        language = lang.strings[code]
        text = ("✅ " if using else "") + language["NAME"]
        data = "noop" if using else f"manage set lang {anime_id} {page} {code}"
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)
    keyboard.append([(lang.back_button, f"manage episodes {anime_id} {page}")])

    await callback.edit_message_text(lang.settings_language, reply_markup=ikb(keyboard))


@Amime.on_callback_query(
    filters.regex(r"^manage set lang (?P<id>\d+) (?P<page>\d+) (?P<code>\w+)")
)
async def manage_set_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    code = callback.matches[0]["code"]
    user = callback.from_user

    LANGUAGE[str(user.id)][str(anime_id)] = code

    await manage_lang_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"^manage add episode (?P<id>\d+) (?P<page>\d+)")
)
async def manage_add_episode_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    await callback.edit_message_text(lang.list_of_questions)

    answers: List[Message] = []

    answer = await chat.ask(lang.send_me_the(item=lang.video.lower()), filters.video)
    answers.append(answer)
    video = answer.video

    language = LANGUAGE[str(user.id)][str(anime_id)]
    answer = await chat.ask(
        lang.send_me_the(item=lang.episode_number.lower()), filters.regex(r"^\d+")
    )
    number = int(answer.text)
    answers.append(answer)
    while (
        len(await Episodes.filter(anime=anime_id, number=number, language=language)) > 0
    ):
        answers.append(await answer.reply_text(lang.duplicate_episode_number))
        answer = await chat.ask(
            lang.send_me_the(item=lang.episode_number.lower()), filters.regex(r"^\d+")
        )
        number = int(answer.text)
        answers.append(answer)

    answer = await chat.ask(
        lang.send_me_the(item=lang.duration.lower() + " (m)"), filters.regex(r"^\d+")
    )
    duration = int(answer.text)
    answers.append(answer)

    await Episodes.create(
        anime=anime_id,
        file_id=video.file_id,
        number=number,
        duration=duration,
        language=language,
    )

    for answer in answers:
        try:
            await answer.delete()
        except:
            pass
        try:
            await answer.request.delete()
        except:
            pass

    await callback.edit_message_text(
        lang.episode_added,
        reply_markup=ikb([[(lang.back_button, f"manage episodes {anime_id} {page}")]]),
    )


@Amime.on_callback_query(
    filters.regex(r"^manage del (?P<id>\d+) (?P<number>\d+) (?P<page>\d+)")
)
async def manage_del_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    number = int(callback.matches[0]["number"])
    user = callback.from_user

    try:
        episode = await Episodes.get(
            anime=anime_id,
            number=number,
            language=LANGUAGE[str(user.id)][str(anime_id)],
        )
        await episode.delete()
    except:
        pass

    await manage_episodes_callback(bot, callback)
