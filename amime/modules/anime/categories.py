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


@Amime.on_callback_query(filters.regex(r"^categories anime (?P<page>\d+)"))
async def anime_categories(bot: Amime, callback: CallbackQuery):
    page = int(callback.matches[0]["page"])

    message = callback.message
    lang = callback._lang

    # fmt: off
    categories = [
        "action", "shounen",
        "martial_arts", "adventure",
        "comedy", "ecchi",
        "devils", "drama",
        "fantasy", "yuri",
        "yaoi", "school",
        "sports", "space",
        "hentai", "isekai",
        "shoujo", "fight",
        "mystery", "supernatural",
        "music", "slice_of_life",
    ]
    categories.sort()
    # fmt: on

    layout = Pagination(
        categories,
        item_data=lambda i, pg: f"categorie anime {i} 1",
        item_title=lambda i, pg: lang.strings[lang.code][i],
        page_data=lambda pg: f"categories anime {pg}",
    )

    lines = layout.create(page, lines=8, columns=2)

    keyboard = []
    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, "anime")])

    await message.edit_text(
        lang.categories_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"^categorie anime (?P<categorie>\w+) (?P<page>\d+)")
)
async def anime_categorie(bot: Amime, callback: CallbackQuery):
    categorie = callback.matches[0]["categorie"]
    page = int(callback.matches[0]["page"])

    message = callback.message
    lang = callback._lang

    genre = categorie.replace("_", " ")
    results = await anilist.AsyncClient().search(genre, "anime", 50)

    layout = Pagination(
        results,
        item_data=lambda i, pg: f"anime {i.id}",
        item_title=lambda i, pg: i.title.romaji,
        page_data=lambda pg: f"categorie anime {categorie} {pg}",
    )

    lines = layout.create(page, lines=8)

    keyboard = []
    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, "categories anime 1")])

    await message.edit_text(
        lang.categorie_text.format(genre=lang.strings[lang.code][categorie]),
        reply_markup=ikb(keyboard),
    )
