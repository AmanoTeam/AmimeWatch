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
from pyrogram.types import CallbackQuery, Message, User
from pyromod.helpers import ikb
from typing import Dict, List, Union

from ..amime import Amime
from ..database import Collaborators, Users


@Amime.on_message(filters.cmd(r"(collabs|collaborators)$"))
async def collaborators_message(bot: Amime, message: Message):
    await collaborators_union(bot, message)


@Amime.on_callback_query(filters.regex(r"collaborators"))
async def collaborators_callback(bot: Amime, callback: CallbackQuery):
    await collaborators_union(bot, callback)


async def collaborators_union(bot: Amime, union: Union[CallbackQuery, Message]):
    lang = union._lang
    is_callback = isinstance(union, CallbackQuery)

    text = lang.collaborators(bot_name=bot.me.first_name)

    users = await Users.filter(is_collaborator=True)

    for user in users:
        languages: List[str] = []
        collaborator = await Collaborators.filter(user=user.id)
        for item in collaborator:
            languages.append(item.language)
        username = (
            f"@{user.username}" if len(user.username) > 0 else f"<b>{user.name}</b>"
        )
        text += f"    {username} (<i>{', '.join(languages)}</i>)\n"

    kwargs: Dict = {}
    if is_callback:
        kwargs["reply_markup"] = ikb([[(lang.back_button, "about")]])

    await (union.edit_message_text if is_callback else union.reply_text)(text, **kwargs)


@Amime.on_message(
    filters.cmd(r"(collab|collaborator) add (?P<languages>.+)")
    & filters.reply
    & filters.sudo
)
async def collab_add(bot: Amime, message: Message):
    languages = message.matches[0]["languages"].split()
    reply = message.reply_to_message
    user = reply.from_user
    lang = message._lang

    already_in: List[str] = []
    promoted_in: List[str] = []
    not_found: List[str] = []

    if bot.is_sudo(user):
        await message.reply_text(lang.user_is_sudo.format(mention=user.mention()))
        return
    else:
        try:
            user_db = await Users.get(id=user.id)
            user_db.update_from_dict({"is_collaborator": True})
            await user_db.save()
        except:
            user_db = await Users.create(
                id=user.id,
                name=user.first_name,
                username=user.username or "",
                language_bot=user.language_code or "en-US",
                language_anime=user.language_code or "en-US",
                is_collaborator=True,
            )

        for language in languages:
            if language not in lang.strings.keys():
                not_found.append(language)
            else:
                if (
                    len(await Collaborators.filter(user=user.id, language=language))
                    == 0
                ):
                    await Collaborators.create(user=user.id, language=language)
                    promoted_in.append(language)
                else:
                    already_in.append(language)

        if len(already_in) == len(languages):
            await message.reply_text(
                lang.is_already_a_collaborator_in_all_these_languages.format(
                    mention=user.mention()
                )
            )
            return
        else:
            text = ""
            if len(promoted_in) > 0:
                text += lang.promoted_to_collaborator.format(
                    mention_sudo=message.from_user.mention(),
                    mention_user=user.mention(),
                    languages=", ".join(promoted_in),
                )

            if len(already_in) > 0:
                text += lang.is_already_a_collaborator_in_some_languages(
                    languages=", ".join(already_in)
                )

            if len(not_found) > 0:
                text += lang.languages_not_exists(languages=", ".join(not_found))

            await message.reply_text(text)


@Amime.on_message(
    filters.cmd(r"(collab|collaborator) del (?P<languages>.+)")
    & filters.reply
    & filters.sudo
)
async def collab_del(bot: Amime, message: Message):
    languages = message.matches[0]["languages"].split()
    reply = message.reply_to_message
    user = reply.from_user
    lang = message._lang

    not_promoted_in: List[str] = []
    demoted_in: List[str] = []
    not_found: List[str] = []

    if bot.is_sudo(user):
        await message.reply_text(lang.user_is_sudo.format(mention=user.mention()))
        return
    else:
        try:
            user_db = await Users.get(id=user.id)
        except:
            user_db = await Users.create(
                id=user.id,
                name=user.first_name,
                username=user.username or "",
                language_bot=user.language_code or "en-US",
                language_anime=user.language_code or "en-US",
                is_collaborator=False,
            )
            await message.reply_text(
                lang.is_not_a_collaborator_in_all_of_these_languages.format(
                    mention=user.mention()
                )
            )
            return

        collaborator_in: List[str] = [
            collaborator.language
            for collaborator in await Collaborators.filter(user=user.id)
        ]

        for language in languages:
            if language not in lang.strings.keys():
                not_found.append(language)
            else:
                collab = await Collaborators.filter(user=user.id, language=language)
                if len(collab) > 0:
                    await collab[0].delete()
                    demoted_in.append(language)
                else:
                    not_promoted_in.append(language)

        if len(collaborator_in) == len(demoted_in):
            user_db.update_from_dict({"is_collaborator": False})
            await user_db.save()

        if len(not_promoted_in) == len(languages):
            await message.reply_text(
                lang.is_not_a_collaborator_in_all_of_these_languages.format(
                    mention=user.mention()
                )
            )
            return
        else:
            text = ""
            if len(demoted_in) > 0:
                text += lang.demoted_collaborator.format(
                    mention_sudo=message.from_user.mention(),
                    mention_user=user.mention(),
                    languages=", ".join(demoted_in),
                )

            if len(not_promoted_in) > 0:
                text += lang.is_not_a_collaborator_in_some_languages(
                    languages=", ".join(not_promoted_in)
                )

            if len(not_found) > 0:
                text += lang.languages_not_exists(languages=", ".join(not_found))

            await message.reply_text(text)
