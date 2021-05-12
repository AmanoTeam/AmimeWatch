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

import anilist
from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.database import Requests, Users


@Amime.on_callback_query(filters.regex(r"^request get (\w+) (\d+) (\w+)"))
async def request_get(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    content_type = callback.matches[0].group(1)
    content_id = int(callback.matches[0].group(2))
    language = callback.matches[0].group(3)

    text_splited = message.text.html.splitlines()
    text = "\n".join(text_splited[: len(text_splited) - 2])
    text += f"\n<b>Caught by</b>: {user.mention()}"
    text += "\n\n#REQUEST"

    await message.edit_text(
        text,
        reply_markup=ikb(
            [
                [
                    (
                        "↩️ Drop",
                        f"request drop {content_type} {content_id} {language} {user.id}",
                    ),
                    (
                        "✅ Done",
                        f"request done {content_type} {content_id} {language} {user.id}",
                    ),
                ]
            ]
        ),
    )


@Amime.on_callback_query(filters.regex(r"^request drop (\w+) (\d+) (\w+) (\d+)"))
async def request_drop(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    content_type = callback.matches[0].group(1)
    content_id = int(callback.matches[0].group(2))
    language = callback.matches[0].group(3)
    user_id = int(callback.matches[0].group(4))

    if not bot.is_sudo(user):
        if user_id != user.id:
            return

    text_splited = message.text.html.splitlines()
    text = "\n".join(text_splited[: len(text_splited) - 3])
    text += "\n\n#REQUEST"

    await message.edit_text(
        text,
        reply_markup=ikb(
            [[("🆙 Get", f"request get {content_type} {content_id} {language}")]]
        ),
    )


@Amime.on_callback_query(filters.regex(r"^request done (\w+) (\d+) (\w+) (\d+)"))
async def request_done(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    content_type = callback.matches[0].group(1)
    content_id = int(callback.matches[0].group(2))
    language = callback.matches[0].group(3)
    user_id = int(callback.matches[0].group(4))

    if not bot.is_sudo(user):
        if user_id != user.id:
            return

    content = await anilist.AsyncClient().get(content_id, content_type)

    notified_users = []
    requests = await Requests.filter(item=content_id, type=content_type)
    for request in requests:
        if request.user in notified_users:
            await request.delete()
            continue

        user_db = await Users.get(id=request.user)
        lang = lang.get_language(user_db.language_bot)

        request.update_from_dict({"done": True})
        await request.save()

        try:
            await bot.send_message(
                request.user,
                lang.request_content_done_text(
                    title=content.title.romaji,
                    type=content_type.upper(),
                ),
                reply_markup=ikb(
                    [[(lang.view_more_button, f"{content_type} {content_id}")]]
                ),
            )
        except BaseException:
            pass
        else:
            notified_users.append(request.user)

    await message.edit_text(
        message.text.html + " #DONE",
    )
