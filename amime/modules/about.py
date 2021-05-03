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

from typing import Dict, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.config import CHANNELS, GROUPS


@Amime.on_message(filters.cmd(r"about$"))
@Amime.on_callback_query(filters.regex(r"^about$"))
async def about(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    user = union.from_user
    lang = union._lang

    kwargs: Dict = {}

    is_private = await filters.private(bot, message)
    if is_private and is_callback:
        keyboard = [
            [
                (lang.back_button, "start"),
            ],
        ]
        kwargs["reply_markup"] = ikb(keyboard)

    await (message.edit_text if is_callback else message.reply_text)(
        lang.about_text.format(
            bot_name=bot.me.first_name,
            github="<a href='https://github.com/AmanoTeam/AmimeWatch'>GitHub</a>",
            channel=f"<a href='https://t.me/c/{str(CHANNELS[lang.code])[4:]}/-1'>{lang.channel}</a>",
            group=f"<a href='https://t.me/c/{str(GROUPS[lang.code])[4:]}/-1'>{lang.group}</a>",
        ),
        disable_web_page_preview=True,
        **kwargs,
    )
