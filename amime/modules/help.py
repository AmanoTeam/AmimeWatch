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
from pyromod.helpers import ikb
from typing import Dict, Union

from ..amime import Amime


@Amime.on_message(filters.cmd(r"help$"))
async def help_message(bot: Amime, message: Message):
    lang = message._lang

    if await filters.private(bot, message):
        await help_union(bot, message)
    else:
        await message.reply_text(
            lang.help_in_pm,
            reply_markup=ikb(
                [
                    [
                        (
                            lang.help_button,
                            f"https://t.me/{bot.me.username}?start=help",
                            "url",
                        )
                    ]
                ]
            ),
        )


@Amime.on_callback_query(filters.regex(r"^help$"))
async def help_callback(bot: Amime, callback: CallbackQuery):
    await help_union(bot, callback)


async def help_union(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    lang = union._lang

    keyboard = [
        [(lang.anime_button, "help anime"), (lang.manga_button, "help manga")],
        [(lang.inline_button, "help inline")],
    ]

    if is_callback:
        keyboard.append([(lang.back_button, "start")])

    await (union.edit_message_text if is_callback else union.reply_text)(
        lang.help,
        reply_markup=ikb(keyboard),
        disable_web_page_preview=True,
    )


@Amime.on_message(filters.cmd(r"help (?P<module>.+)") & filters.private)
async def help_module_message(bot: Amime, message: Message):
    await help_module_union(bot, message)


@Amime.on_callback_query(filters.regex(r"help (?P<module>.+)"))
async def help_module_callback(bot: Amime, callback: CallbackQuery):
    await help_module_union(bot, callback)


async def help_module_union(bot: Amime, union: Union[CallbackQuery, Message]):
    module_name = union.matches[0]["module"]
    is_callback = isinstance(union, CallbackQuery)
    lang = union._lang

    kwargs: Dict = {}
    if is_callback:
        kwargs["reply_markup"] = ikb([[(lang.back_button, "help")]])

    module_help_name = f"{module_name}_help"
    if module_help_name in lang.strings[lang.code].keys():
        text = lang.strings[lang.code][module_help_name]

        await (union.edit_message_text if is_callback else union.reply_text)(
            text.format(
                anilist="<a href='https://anilist.co'>Anilist</a>",
                bot_username=bot.me.username,
                request_episodes_button=lang.request_episodes_button,
            ),
            disable_web_page_preview=True,
            **kwargs,
        )
    else:
        await (union.edit_message_text if is_callback else union.reply_text)(
            lang.not_found(
                type=lang.module.lower(), key=lang.name.lower(), value=module_name
            ),
            disable_web_page_preview=True,
            **kwargs,
        )
