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

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import array_chunk, ikb
from typing import Dict

from amime.amime import Amime
from amime.database import Collaborators, Episodes, Users


@Amime.on_message(filters.cmd(r"user"))
async def user_view(bot: Amime, message: Message):
    reply = message.reply_to_message
    lang = message._lang

    me = message.from_user

    text = message.text
    query = text.split()

    if len(query) > 1:
        user = await bot.get_users(query[1])
    elif bool(reply):
        user = reply.from_user
    else:
        user = me

    user_db = await Users.get(id=user.id)

    is_collaborator = user_db.is_collaborator or bot.is_sudo(user)
    if is_collaborator:
        episodes = await Episodes.filter(added_by=user.id)

    text = f"<b>{user.mention()}</b>"
    text += f"\n<b>{lang.user_informations}</b>:"
    text += f"\n    <b>{lang.language}</b>: <code>{lang.strings[user_db.language_bot]['LANGUAGE_NAME']}</code>"
    text += f"\n    <b>{lang.collaborator}</b>: <code>{lang.yes if is_collaborator else lang.no}</code>"
    if is_collaborator:
        text += f"\n    <b>{lang.episodes_added}</b>: <code>{len(episodes)}</code>"

    kwargs: Dict = {}
    if await filters.sudo(bot, message) and user.id != me.id:
        keyboard = [
            [
                (lang.collaborator_button, f"user collaborator {user.id}"),
            ]
        ]

        kwargs["reply_markup"] = ikb(keyboard)

    await message.reply_text(text, **kwargs)


@Amime.on_callback_query(filters.regex(r"^user collaborator (\d+)") & filters.sudo)
async def user_collaborator(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    user = await bot.get_users(callback.matches[0].group(1))

    buttons = []
    for code, obj in lang.strings.items():
        in_language = await Collaborators.get_or_none(user=user.id, language=code)
        text = ("✅ " if in_language is not None else "") + obj["LANGUAGE_NAME"]
        data = f"user collaborator edit {user.id} {code}"
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    text = f"<b>{user.mention()}</b>"
    text += f"\n{lang.language_text}"

    await message.edit_text(
        text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"^user collaborator edit (\d+) (\w+)") & filters.sudo
)
async def user_collaborator_edit(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    user_id = int(callback.matches[0].group(1))
    language = callback.matches[0].group(2)

    collaborator = await Collaborators.get_or_none(user=user_id, language=language)
    if collaborator is None:
        await Collaborators.create(user=user_id, language=language)
    else:
        await collaborator.delete()

    await user_collaborator(bot, callback)
