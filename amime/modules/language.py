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
from typing import List, Tuple

from ..amime import Amime
from ..database import Chats, Users


@Amime.on_callback_query(filters.regex(r"^language (?P<type>bot|group)"))
async def language_callback(bot: Amime, callback: CallbackQuery):
    language_type = callback.matches[0]["type"]
    chat = callback.message.chat
    user = callback.from_user
    lang = callback._lang

    if language_type == "group":
        if not await filters.administrator(bot, callback):
            return
        db = await Chats.get(id=chat.id)
    else:
        db = await Users.get(id=user.id)

    buttons: List[Tuple] = []
    for code, obj in lang.strings.items():
        text, data = (
            (f"✅ {obj['NAME']}", "noop")
            if obj["LANGUAGE_CODE"]
            == (db.language if language_type == "group" else db.language_bot)
            else (obj["NAME"], f"language set {language_type} {obj['LANGUAGE_CODE']}")
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)
    keyboard.append([(lang.back_button, "settings")])

    await callback.edit_message_text(lang.settings_language, reply_markup=ikb(keyboard))


@Amime.on_callback_query(
    filters.regex(r"^language set (?P<type>bot|group) (?P<code>.+)")
)
async def language_set_callback(bot: Amime, callback: CallbackQuery):
    language_type = callback.matches[0]["type"]
    language_code = callback.matches[0]["code"]
    chat = callback.message.chat
    user = callback.from_user
    lang = callback._lang

    if language_type == "group":
        if not await filters.administrator(bot, callback):
            return
        db = await Chats.get(id=chat.id)
        db.update_from_dict({"language": language_code})
        await db.save()
    else:
        db = await Users.get(id=user.id)
        db.update_from_dict({f"language_{language_type}": language_code})
        await db.save()

    callback._lang = lang.get_language(language_code)

    callback.matches = [{"type": language_type}]
    await language_callback(bot, callback)
