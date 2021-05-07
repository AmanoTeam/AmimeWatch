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

import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Animation, Document, Message, Photo, Sticker, Video

from amime.amime import Amime
from amime.config import CHANNELS, CHATS
from amime.database import Chats, Users


@Amime.on_message(
    filters.cmd(r"alert (\w+) (\w+)")
    & (filters.collaborator | filters.sudo)
    & filters.chat(CHATS["staff"])
)
async def alert(bot: Amime, message: Message):
    reply = message.reply_to_message
    lang = message._lang

    to = message.matches[0].group(1)
    language = message.matches[0].group(2)

    media = message.photo or message.animation or message.document or message.video
    text = " ".join((message.text or message.caption).split()[3:])

    if len(text) == 0:
        if bool(reply):
            media = (
                reply.photo
                or reply.sticker
                or reply.animation
                or reply.document
                or reply.video
            )
            text = reply.text or reply.caption

    if len(text) == 0:
        await message.reply_text(lang.empty_message_text)
        return

    chats = []

    if to in ["groups", "all"]:
        chats += [chat.id for chat in await Chats.filter(language=language)]
    if to in ["users", "all"]:
        chats += [user.id for user in await Users.filter(language_bot=language)]

    if len(chats) == 0:
        await message.reply_text(lang.no_chat_found_text)
    else:
        sent = await message.reply_text(lang.sending_alert_text)

        success = []
        failed = []
        for chat in chats:
            if chat in CHATS.values() or chat in CHANNELS.values():
                continue

            try:
                if media is not None:
                    if isinstance(media, Animation):
                        await bot.send_animation(chat, media.file_id, text)
                    elif isinstance(media, Document):
                        await bot.send_document(
                            chat, media.file_id, caption=text, force_document=True
                        )
                    elif isinstance(media, Photo):
                        await bot.send_photo(chat, media.file_id, text)
                    elif isinstance(media, Video):
                        await bot.send_video(chat, media.file_id, text)
                    elif isinstance(media, Sticker):
                        await bot.send_sticker(chat, media.file_id)

                    success.append(chat)
                    continue

                await bot.send_message(chat, text)

                success.append(chat)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except BaseException:
                failed.append(chat)

        await sent.edit_text(
            lang.alert_sent_text(
                success=len(success),
                failed=len(failed),
            ),
        )
