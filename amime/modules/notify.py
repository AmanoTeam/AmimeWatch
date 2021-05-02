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
from pyrogram.types import Chat, CallbackQuery, User
from pyromod.helpers import bki, ikb
from typing import Tuple, Union

from amime.amime import Amime
from amime.database import Notify


async def get_notify_button(
    lang, recipient: Union[Chat, User], content_type: str, content_id: int
) -> Tuple:
    recipient_type = "user" if isinstance(recipient, User) else "group"

    notify = await Notify.get_or_none(
        recipient=recipient.id,
        recipient_type=recipient_type,
        item=content_id,
        type=content_type,
    )
    if notify is None:
        status = "🔔"
    else:
        status = "🔕"
    return (
        f"{status} {lang.notify}",
        f"notify {content_type} {content_id} {recipient_type} {recipient.id}",
    )


@Amime.on_callback_query(
    filters.regex(
        r"^notify (?P<c_type>\w+) (?P<c_id>\d+) (?P<r_type>\w+) (?P<r_id>(?:\-)?\d+)"
    )
)
async def notify_callback(bot: Amime, callback: CallbackQuery):
    content_type = callback.matches[0]["c_type"]
    content_id = int(callback.matches[0]["c_id"])
    recipient_type = callback.matches[0]["r_type"]
    recipient_id = int(callback.matches[0]["r_id"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    if recipient_type == "group":
        if not await filters.administrator(bot, callback):
            return

    notify = await Notify.get_or_none(
        recipient=recipient_id,
        recipient_type=recipient_type,
        item=content_id,
        type=content_type,
    )

    if notify is None:
        await Notify.create(
            recipient=recipient_id,
            recipient_type=recipient_type,
            item=content_id,
            type=content_type,
        )
        await callback.answer(lang.notifications_linked_alert, show_alert=True)
    else:
        await notify.delete()
        await callback.answer(lang.notifications_turned_off_alert, show_alert=True)

    keyboard = bki(message.reply_markup)

    for line, column in enumerate(keyboard):
        for index, button in enumerate(column):
            if button[1].startswith("notify"):
                keyboard[line][index] = await get_notify_button(
                    lang,
                    user if recipient_type == "user" else chat,
                    content_type,
                    content_id,
                )

    await callback.edit_message_reply_markup(ikb(keyboard))
