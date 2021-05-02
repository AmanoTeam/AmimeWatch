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
from pyromod.nav import Pagination

from amime.amime import Amime
from amime.database import Favorites


@Amime.on_callback_query(filters.regex(r"favorites manga (?P<page>\d+)"))
async def manga_favorites(bot: Amime, callback: CallbackQuery):
    page = int(callback.matches[0]["page"])

    message = callback.message
    user = callback.from_user
    lang = callback._lang

    keyboard = []
    async with anilist.AsyncClient() as client:
        favorites = await Favorites.filter(user=user.id, type="manga")

        results = []
        for favorite in favorites:
            manga = await client.get(favorite.item, "manga")
            results.append((favorite, manga))

        layout = Pagination(
            results,
            item_data=lambda i, pg: f"manga {i[0].item}",
            item_title=lambda i, pg: i[1].title.romaji,
            page_data=lambda pg: f"favorites manga {pg}",
        )

        lines = layout.create(page, lines=8)

        if len(lines) > 0:
            keyboard += lines

    keyboard.append([(lang.back_button, "manga")])

    await message.edit_text(
        lang.favorites_text,
        reply_markup=ikb(keyboard),
    )
