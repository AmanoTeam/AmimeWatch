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

from typing import Dict, List, Tuple, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.database import Chats, Collaborators, Episodes, Users


@Amime.on_message(filters.cmd(r"language$"))
@Amime.on_callback_query(filters.regex(r"^language$"))
async def language(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    chat = message.chat
    user = union.from_user
    lang = union._lang
    current_code: str = "en"

    is_private = await filters.private(bot, message)
    if not is_private:
        if not await filters.administrator(bot, union):
            return
        current_code = (await Chats.get(id=chat.id)).language
    else:
        current_code = (await Users.get(id=user.id)).language_bot

    buttons: List[Tuple] = []
    for code, obj in lang.strings.items():
        text, data = (
            (f"✅ {obj['LANGUAGE_NAME']}", "noop")
            if obj["LANGUAGE_CODE"] == current_code
            else (obj["LANGUAGE_NAME"], f"language set {obj['LANGUAGE_CODE']}")
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    if is_private:
        keyboard.append([(lang.back_button, "start")])

    await (message.edit_text if is_callback else message.reply_text)(
        lang.language_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^language set (?P<code>\w+)"))
async def language_set(bot: Amime, callback: CallbackQuery):
    code = callback.matches[0]["code"]

    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    kwargs: Dict = {}

    is_private = await filters.private(bot, message)
    if not is_private:
        if not await filters.administrator(bot, callback):
            return
        chat_db = await Chats.get(id=chat.id)
        chat_db.update_from_dict({"language": code})
        await chat_db.save()
    else:
        user_db = await Users.get(id=user.id)
        user_db.update_from_dict({"language_bot": code})
        await user_db.save()

        keyboard = [
            [(lang.back_button, "start")],
        ]
        kwargs["reply_markup"] = ikb(keyboard)

    await message.edit_text(
        lang.strings[code]["language_changed_text"],
        **kwargs,
    )


@Amime.on_callback_query(
    filters.regex(
        r"^manage (?P<content_type>anime|manga) language (\d+) (\d+) (\d+) (\w+) (\d+)"
    )
)
async def language_manage(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    content_type = callback.matches[0]["content_type"]
    content_id = int(callback.matches[0].group(2))
    season = int(callback.matches[0].group(3))
    subtitled = bool(int(callback.matches[0].group(4)))
    language = callback.matches[0].group(5)
    page = int(callback.matches[0].group(6))

    languages = []
    if await filters.sudo(bot, callback):
        languages = [*lang.strings.keys()]
    else:
        for collaborator in await Collaborators.filter(user=user.id):
            if collaborator.language not in languages:
                languages.append(collaborator.language)

    buttons: List[Tuple] = []
    for _language in languages:
        text = (
            "✅" if _language == language else ""
        ) + f" {lang.strings[_language]['LANGUAGE_NAME']}"
        data = (
            "noop"
            if _language == language
            else f"manage {content_type} language {content_id} {season} {int(subtitled)} {_language} 1"
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    keyboard.append(
        [
            (
                lang.back_button,
                f"manage {content_type} {content_id} {season} {int(subtitled)} {language} {page}",
            )
        ]
    )

    await message.edit_text(
        lang.language_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^episodes language (\d+) (\d+) (\w+) (\d+)"))
async def language_episodes(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    language = callback.matches[0].group(3)
    page = int(callback.matches[0].group(4))

    user_db = await Users.get(id=user.id)
    if not user_db.language_anime == language:
        user_db.update_from_dict({"language_anime": language})
        await user_db.save()

    episodes = await Episodes.filter(anime=anime_id)
    episodes = sorted(episodes, key=lambda episode: episode.number)

    languages = []
    for episode in episodes:
        if episode.language not in languages:
            languages.append(episode.language)

    buttons: List[Tuple] = []
    for _language in languages:
        text = (
            "✅" if _language == language else ""
        ) + f" {lang.strings[_language]['LANGUAGE_NAME']}"
        data = (
            "noop"
            if _language == language
            else f"episodes language {anime_id} {season} {_language} 1"
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    keyboard.append([(lang.back_button, f"episodes {anime_id} {season} {page}")])

    await message.edit_text(
        lang.language_text,
        reply_markup=ikb(keyboard),
    )
