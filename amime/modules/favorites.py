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

import anilist

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, User
from pyromod.helpers import ikb
from pyromod.nav import Pagination
from typing import Dict, Optional, Tuple, Union

from ..amime import Amime
from ..database import Favorites


@Amime.on_message(filters.cmd(r"(my)?favorites") & filters.private)
async def favorites_message(bot: Amime, message: Message):
    await favorites_union(bot, message)


@Amime.on_callback_query(filters.regex(r"favorites$"))
async def favorites_callback(bot: Amime, callback: CallbackQuery):
    await favorites_union(bot, callback)


async def favorites_union(bot: Amime, union: Union[CallbackQuery, Message]):
    lang = union._lang
    is_callback = isinstance(union, CallbackQuery)

    keyboard = [
        [
            (lang.anime_button, "favorites anime 1"),
            (lang.manga_button, "favorites manga 1"),
        ]
    ]

    if is_callback:
        keyboard.append([(lang.back_button, "start")])

    await (union.edit_message_text if is_callback else union.reply_text)(
        lang.favorites, reply_markup=ikb(keyboard)
    )


@Amime.on_callback_query(filters.regex(r"^favorites (?P<type>\w+) (?P<page>\d+)"))
async def favorites_content_callback(bot: Amime, callback: CallbackQuery):
    content_type = callback.matches[0]["type"]
    page = int(callback.matches[0]["page"])
    await favorites_content_union(bot, callback, content_type, page)


async def favorites_content_union(
    bot: Amime,
    union: Union[CallbackQuery, Message],
    content_type: str,
    page: Optional[int] = 1,
):
    lang = union._lang
    user = union.from_user
    is_callback = isinstance(union, CallbackQuery)

    favorites = await Favorites.filter(user=user.id, type=content_type)

    favorites_dict: Dict = {}
    for favorite in favorites:
        async with anilist.AsyncClient() as client:
            content = await client.get(favorite.item, content_type)
        favorites_dict[favorite.id] = [favorite, content]

    def item_title(i, pg) -> str:
        return i[1][1].title.romaji

    layout = Pagination(
        [*favorites_dict.items()],
        item_data=lambda i, pg: f"{content_type} {i[1][0].item}",
        item_title=item_title,
        page_data=lambda pg: f"favorites {content_type} {pg}",
    )

    lines = layout.create(page, lines=8)

    keyboard = []
    if len(lines) > 0:
        keyboard += lines

    if is_callback:
        keyboard.append([(lang.back_button, "favorites")])

    if len(lines) > 0:
        await union.edit_message_text(
            lang.favorites_list(type=f"{content_type}s"),
            reply_markup=ikb(keyboard),
        )
    else:
        await union.edit_message_text(
            lang.favorites_empty(type=f"{content_type}s"),
            reply_markup=ikb(keyboard),
        )


async def get_favorite_button(
    lang, user: User, content_type: str, content_id: int
) -> Tuple:
    if (
        len(await Favorites.filter(user=user.id, item=content_id, type=content_type))
        > 0
    ):
        status = "🌟"
    else:
        status = "⭐"
    return (f"{status} {lang.favorite}", f"favorite {content_type} {content_id}")


@Amime.on_callback_query(filters.regex(r"favorite (?P<type>\w+) (?P<id>\d+)"))
async def favorite_callback(bot: Amime, callback: CallbackQuery):
    content_type = callback.matches[0]["type"]
    content_id = int(callback.matches[0]["id"])
    lang = callback._lang
    user = callback.from_user
    message = callback.message

    favorite = await Favorites.filter(user=user.id, item=content_id, type=content_type)

    if len(favorite) > 0:
        favorite = favorite[0]
        await favorite.delete()
        await callback.answer(
            lang.removed_from_favorites(type=content_type), show_alert=True
        )
    else:
        await Favorites.create(user=user.id, item=content_id, type=content_type)
        await callback.answer(
            lang.added_to_favorites(type=content_type), show_alert=True
        )

    keyboard = []
    lines = message.reply_markup.inline_keyboard
    index = 0
    for line in lines:
        keyboard.append([])
        for button in line:
            if button["url"]:
                keyboard[index].append((button["text"], button["url"], "url"))
            else:
                keyboard[index].append((button["text"], button["callback_data"]))
        index += 1

    for line, column in enumerate(keyboard):
        for index, button in enumerate(column):
            if button[1].startswith("favorite"):
                keyboard[line][index] = await get_favorite_button(
                    lang, user, content_type, content_id
                )

    await callback.edit_message_reply_markup(ikb(keyboard))
