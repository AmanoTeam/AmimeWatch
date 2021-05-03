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

import re
from typing import Callable, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from amime.database import Users


def load(bot):
    def filter_cmd(pattern: str, *args, **kwargs) -> Callable:
        prefixes = ["!", "/"]
        prefix = f"[{re.escape(''.join(prefixes))}]"
        pattern_splited = pattern.split()
        command = pattern_splited[0] + f"((?i)@{bot.me.username})?"
        if "$" in command:
            command = command.replace("$", "")
            command += "$"
        if len(pattern_splited) > 1:
            command += " "
        pattern = command + " ".join(pattern_splited[1:])
        return filters.regex(r"^" + prefix + pattern, *args, **kwargs)

    async def filter_sudo(_, bot, union: Union[CallbackQuery, Message]) -> Callable:
        user = union.from_user
        if not user:
            return False
        return bot.is_sudo(user)

    async def filter_collaborator(_, bot, union: Union[CallbackQuery, Message]) -> bool:
        user = union.from_user
        if not user:
            return False
        return (await Users.get(id=user.id)).is_collaborator

    async def filter_administrator(
        _, bot, union: Union[CallbackQuery, Message]
    ) -> bool:
        is_callback = isinstance(union, CallbackQuery)
        message = union.message if is_callback else union
        chat = message.chat
        user = union.from_user

        member = await bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]

    filters.cmd = filter_cmd
    filters.sudo = filters.create(filter_sudo, "FilterSudo")
    filters.administrator = filters.create(filter_administrator, "FilterAdministrator")
    filters.collaborator = filters.create(filter_collaborator, "FilterCollaborator")
