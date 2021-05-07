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
from pyrogram.types import CallbackQuery, InputMediaPhoto
from pyromod.helpers import array_chunk, ikb
from pyromod.nav import Pagination

from amime.amime import Amime
from amime.database import Episodes, Users, Viewed, Watched


@Amime.on_callback_query(filters.regex(r"^episodes (\d+) (\d+) (\d+)"))
async def anime_episodes(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    page = int(callback.matches[0].group(3))

    user_db = await Users.get(id=user.id)
    language = user_db.language_anime

    keyboard = [
        [
            (
                f"{lang.language_button}: {lang.strings[language]['LANGUAGE_NAME']}",
                f"episodes language {anime_id} {season} {language} {page}",
            ),
        ],
    ]

    if season > 0:
        keyboard[-1].append(
            (
                f"{lang.season_button}: {season}",
                f"episodes season {anime_id} {season} {page}",
            )
        )

    episodes = await Episodes.filter(anime=anime_id, season=season, language=language)
    episodes = sorted(episodes, key=lambda episode: episode.number)

    episodes_list = []
    for episode in episodes:
        viewed = bool(await Viewed.get_or_none(user=user.id, item=episode.id))
        watched = bool(await Watched.get_or_none(user=user.id, episode=episode.id))
        episodes_list.append((episode, viewed, watched))

    layout = Pagination(
        episodes_list,
        item_data=lambda i, pg: f"episode {i[0].anime} {i[0].season} {i[0].number}",
        item_title=lambda i, pg: ("✅" if i[2] else "👁️" if i[1] else "🙈")
        + f" {i[0].number}"
        + (f"-{i[0].unified_until}" if i[0].unified_until > 0 else ""),
        page_data=lambda pg: f"episodes {anime_id} {season} {pg}",
    )

    lines = layout.create(page, lines=5, columns=3)

    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, f"anime {anime_id}")])

    await callback.edit_message_media(
        InputMediaPhoto(
            f"https://img.anili.st/media/{anime_id}",
            caption=lang.watch_list_anime_text,
        ),
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^episodes season (\d+) (\d+) (\d+)"))
async def episodes_season(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    page = int(callback.matches[0].group(3))

    user_db = await Users.get(id=user.id)
    language = user_db.language_anime

    episodes = await Episodes.filter(anime=anime_id, language=language)
    episodes = sorted(episodes, key=lambda episode: episode.number)

    seasons = []
    for episode in episodes:
        if episode.season not in seasons:
            seasons.append(episode.season)

    seasons.sort()

    buttons = []
    for _season in seasons:
        text = ("✅" if _season == season else "") + f" {_season}"
        data = (
            "noop" if _season == season else f"episodes season {anime_id} {_season} 1"
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    keyboard.append([(lang.back_button, f"episodes {anime_id} {season} {page}")])

    await message.edit_text(
        lang.season_text,
        reply_markup=ikb(keyboard),
    )
