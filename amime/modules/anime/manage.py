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

import aioanilist
import os

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from pyromod.helpers import array_chunk, ikb
from pyromod.nav import Pagination
from typing import Dict, List, Tuple

from ...amime import Amime
from ...database import Collaborators, Episodes


ADDING: Dict = {}
LANGUAGE: Dict = {}
SEASON: Dict = {}


@Amime.on_callback_query(filters.regex(r"^manage anime (?P<id>\d+)"))
async def manage_anime_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    user = callback.from_user
    lang = callback._lang

    language = (
        "en"
        if await filters.sudo(bot, callback)
        else (await Collaborators.filter(user=user.id))[-1].language
    )
    LANGUAGE[str(user.id)] = {f"{anime_id}": language}

    episodes = await Episodes.filter(anime=anime_id, language=language)
    episodes = sorted(episodes, key=lambda episode: episode.number)

    SEASON[str(user.id)] = {
        f"{anime_id}": episodes[-1].season if len(episodes) > 0 else 0
    }

    keyboard = [
        [(lang.episodes_button, f"manage episodes {anime_id} 1")],
        [(lang.back_button, f"anime {anime_id}")],
    ]

    await callback.edit_message_text(
        lang.manage_anime,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^manage episodes (?P<id>\d+) (?P<page>\d+)"))
async def manage_episodes_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    language = LANGUAGE[str(user.id)][str(anime_id)]
    season = SEASON[str(user.id)][str(anime_id)]

    keyboard = [
        [
            (lang.add_button, f"manage add episode {anime_id} {page}"),
            (
                f"{lang.language_button}: {lang.strings[language]['NAME']}",
                f"manage lang {anime_id} {page}",
            ),
        ]
    ]

    episodes = await Episodes.filter(anime=anime_id, season=season, language=language)
    episodes = sorted(episodes, key=lambda episode: episode.number)

    keyboard.append(
        [
            (f"{lang.season_button}: {season}", f"manage season {anime_id} {page}"),
            (
                f"{lang.delete_button} {lang.all.lower()}",
                f"manage del season {anime_id} {season} {language} {page}",
            ),
        ]
    )

    episodes_dict: Dict = {}
    for episode in episodes:
        episodes_dict[episode.id] = episode

    def item_title(i, pg) -> str:
        return f"🗑️ {i[1].number}"

    layout = Pagination(
        [*episodes_dict.items()],
        item_data=lambda i, pg: f"manage del episode {i[1].anime} {i[1].number} {pg}",
        item_title=item_title,
        page_data=lambda pg: f"manage episodes {anime_id} {pg}",
    )

    lines = layout.create(page, lines=5, columns=2)

    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, f"manage anime {anime_id}")])

    await callback.edit_message_media(
        InputMediaPhoto(
            f"https://img.anili.st/media/{anime_id}",
            caption=lang.manage_episodes,
        ),
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(filters.regex(r"^manage lang (?P<id>\d+) (?P<page>\d+)"))
async def manage_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    codes = (
        list(lang.strings.keys())
        if await filters.sudo(bot, callback)
        else [
            collab_db.language for collab_db in await Collaborators.filter(user=user.id)
        ]
    )

    buttons: List[Tuple] = []
    for code in codes:
        using = code == LANGUAGE[str(user.id)][str(anime_id)]
        language = lang.strings[code]
        text = ("✅ " if using else "") + language["NAME"]
        data = "noop" if using else f"manage set lang {anime_id} {page} {code}"
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)
    keyboard.append([(lang.back_button, f"manage episodes {anime_id} {page}")])

    await callback.edit_message_text(lang.settings_language, reply_markup=ikb(keyboard))


@Amime.on_callback_query(
    filters.regex(r"^manage set lang (?P<id>\d+) (?P<page>\d+) (?P<code>\w+)")
)
async def manage_set_lang_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    code = callback.matches[0]["code"]
    user = callback.from_user

    LANGUAGE[str(user.id)][str(anime_id)] = code

    await manage_lang_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"^manage add episode (?P<id>\d+) (?P<page>\d+)")
)
async def manage_add_episode_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime = await aioanilist.Client().get("anime", anime_id)

    if not str(user.id) in ADDING.keys():
        ADDING[str(user.id)] = {}
    if not str(anime_id) in ADDING[str(user.id)].keys():
        ADDING[str(user.id)][str(anime_id)] = {}

    adding = ADDING[str(user.id)][str(anime_id)]

    language = LANGUAGE[str(user.id)][str(anime_id)]

    text = lang.preview + "\n"

    text += f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

    keyboard = [[], [], []]

    if "name" in adding.keys():
        text += f"\n<b>{lang.name}</b>: <b>{adding['name']}</b>"
        keyboard[0].append(("✏️ " + lang.name, f"manage add name {anime_id} {page}"))
    else:
        keyboard[0].append(("➕ " + lang.name, f"manage add name {anime_id} {page}"))

    if "number" in adding.keys():
        text += f"\n<b>{lang.episode}</b>: <code>{adding['number']}</code>"
        keyboard[0].append(
            ("✏️ " + lang.episode_number, f"manage add number {anime_id} {page}")
        )
    else:
        keyboard[0].append(
            ("➕ " + lang.episode_number, f"manage add number {anime_id} {page}")
        )

    if "duration" in adding.keys():
        text += f"\n<b>{lang.duration}</b>: <code>{adding['duration']}m</code>"

    if "added_by" in adding.keys() and adding["added_by"]:
        text += f"\n<b>{lang.added_by}</b>: {user.mention()}"
        keyboard[2].append(
            (f"{lang.added_by}: {lang.yes}", f"manage add added_by {anime_id} {page}")
        )
    else:
        keyboard[2].append(
            (f"{lang.added_by}: {lang.no}", f"manage add added_by {anime_id} {page}")
        )

    if "notes" in adding.keys():
        text += f"\n\n<b>{lang.notes}</b>: <i>{adding['notes']}</i>"
        keyboard[1].append(
            ("🗑️ " + lang.notes, f"manage cancel notes {anime_id} {page}")
        )
    else:
        keyboard[1].append(("➕ " + lang.notes, f"manage add notes {anime_id} {page}"))

    keyboard.append(
        [
            (lang.confirm_button, f"manage confirm add {anime_id} {page}"),
            (lang.cancel_button, f"manage cancel episode {anime_id} {page}"),
        ]
    )

    keyboard.append([(lang.back_button, f"manage episodes {anime.id} {page}")])

    if "video" in adding.keys():
        keyboard[1].append(("✏️ " + lang.video, f"manage add video {anime_id} {page}"))
        await callback.edit_message_media(
            InputMediaVideo(
                adding["video"],
                caption=text,
            ),
            reply_markup=ikb(keyboard),
        )
    else:
        keyboard[1].append(("➕ " + lang.video, f"manage add video {anime_id} {page}"))
        await callback.edit_message_media(
            InputMediaPhoto(
                f"https://img.anili.st/media/{anime.id}",
                caption=text,
            ),
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(
    filters.regex(r"manage add (?P<type>\w+) (?P<id>\d+) (?P<page>\d+)")
)
async def add_type_callback(bot: Amime, callback: CallbackQuery):
    add_type = callback.matches[0]["type"]
    add_id = int(callback.matches[0]["id"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    await callback.edit_message_reply_markup({})

    if add_type == "added_by":
        adding = ADDING[str(user.id)][str(add_id)]
        if "added_by" in adding.keys():
            ADDING[str(user.id)][str(add_id)]["added_by"] = not ADDING[str(user.id)][
                str(add_id)
            ]["added_by"]
        else:
            ADDING[str(user.id)][str(add_id)]["added_by"] = True
    elif add_type == "video":
        answer = await chat.ask(
            lang.send_me_the(item=lang.video.lower()), filters.video
        )

        try:
            await answer.delete()
        except:
            pass
        try:
            await answer.request.delete()
        except:
            pass

        ADDING[str(user.id)][str(add_id)][add_type] = answer.video.file_id
        ADDING[str(user.id)][str(add_id)]["duration"] = answer.video.duration // 60
    elif add_type == "season":
        SEASON[str(user.id)][str(add_id)] = SEASON[str(user.id)][str(add_id)] + 1
        await manage_episodes_callback(bot, callback)
        return
    else:
        item = (
            lang.episode_number
            if add_type == "number"
            else lang.strings[lang.code][add_type]
        )

        answer = await chat.ask(lang.send_me_the(item=item.lower()))

        try:
            await answer.delete()
        except:
            pass
        try:
            await answer.request.delete()
        except:
            pass

        ADDING[str(user.id)][str(add_id)][add_type] = answer.text

    await manage_add_episode_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"manage cancel (?P<type>\w+) (?P<id>\d+) (?P<page>\d+)")
)
async def cancel_type_callback(bot: Amime, callback: CallbackQuery):
    cancel_type = callback.matches[0]["type"]
    cancel_id = int(callback.matches[0]["id"])
    user = callback.from_user

    if cancel_type == "episode":
        del ADDING[str(user.id)][str(cancel_id)]
        await manage_episodes_callback(bot, callback)
    elif cancel_type == "notes":
        del ADDING[str(user.id)][str(cancel_id)]["notes"]
        await manage_add_episode_callback(bot, callback)


@Amime.on_callback_query(filters.regex(r"manage confirm add (?P<id>\d+) (?P<page>\d+)"))
async def confirm_add_callback(bot: Amime, callback: CallbackQuery):
    confirm_id = int(callback.matches[0]["id"])
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime = await aioanilist.Client().get("anime", confirm_id)

    adding = ADDING[str(user.id)][str(confirm_id)]
    language = LANGUAGE[str(user.id)][str(confirm_id)]
    season = SEASON[str(user.id)][str(confirm_id)]

    missing = []

    if "video" not in adding.keys():
        missing.append("video")

    if "number" not in adding.keys():
        missing.append("number")

    if len(missing) > 0:
        await callback.answer(
            lang.missing_items_episode(items=", ".join(missing)), show_alert=True
        )
        return

    if (
        len(
            await Episodes.filter(
                anime=confirm_id,
                season=season,
                number=adding["number"],
                language=language,
            )
        )
        > 0
    ):
        await callback.answer(
            lang.duplicate_episode_number,
            show_alert=True,
        )
        return

    await Episodes.create(
        anime=confirm_id,
        file_id=adding["video"],
        name=(adding["name"] if "name" in adding.keys() else ""),
        added_by=(
            user.first_name
            if ("added_by" in adding.keys() and adding["added_by"])
            else ""
        ),
        notes=(adding["notes"] if "notes" in adding.keys() else ""),
        season=season,
        number=adding["number"],
        duration=adding["duration"],
        language=language,
    )

    await callback.answer(lang.episode_added, show_alert=True)

    del ADDING[str(user.id)][str(confirm_id)]

    await manage_episodes_callback(bot, callback)

    try:
        video_path = await bot.download_media(adding["video"])
        video_extension = video_path.split(".")[-1]
        video = (
            await bot.send_video(
                bot.videos_chat.id,
                video_path,
                caption=f"<b>{anime.title.romaji} </b> - {season} - {adding['number']}",
                file_name=f"@{bot.me.username}- {anime.title.romaji} - {season} - {adding['number']}.{video_extension}",
            )
        ).video
        os.remove(video_path)
    except BaseException as excep:
        text = "<b>Error processing an episode</b>\n"
        text += "\n<b>Anime</b>:"
        text += f"\n    <b>ID</b>: <code>{confirm_id}</code>"
        text += "\n\n<b>Episode</b>:"
        if season > 0:
            text += f"\n    <b>Season</b>: <code>{season}</code>"
        text += f"\n    <b>Number</b>: <code>{adding['number']}</code>"
        text += "\n\n<b>Error</b>:"
        text += f"\n    <b>{excep.__class__.__name__}</b>:"
        text += f"\n        <i>{excep}</i>"
        await bot.send_message(bot.staff_chat.id, text)
        return

    episode = await Episodes.get(
        anime=confirm_id,
        season=season,
        number=adding["number"],
        language=language,
    )
    episode.update_from_dict({"file_id": video.file_id})
    await episode.save()


@Amime.on_callback_query(
    filters.regex(r"^manage del episode (?P<id>\d+) (?P<number>\d+) (?P<page>\d+)")
)
async def manage_del_episode_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    number = int(callback.matches[0]["number"])
    page = int(callback.matches[0]["page"])
    lang = callback._lang

    keyboard = [
        [
            (
                lang.confirm_button,
                f"manage confirm del episode {anime_id} {number} {page}",
            ),
            (lang.cancel_button, f"manage episodes {anime_id} {page}"),
        ]
    ]

    await callback.edit_message_text(
        lang.confirm,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(
        r"^manage confirm del episode (?P<id>\d+) (?P<number>\d+) (?P<page>\d+)"
    )
)
async def manage_confirm_del_episode_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    number = int(callback.matches[0]["number"])
    user = callback.from_user

    season = SEASON[str(user.id)][str(anime_id)]

    episode = await Episodes.get(
        anime=anime_id,
        season=season,
        number=number,
        language=LANGUAGE[str(user.id)][str(anime_id)],
    )
    await episode.delete()

    await manage_episodes_callback(bot, callback)


@Amime.on_callback_query(filters.regex(r"^manage season (?P<id>\d+) (?P<page>\d+)"))
async def manage_season_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    keyboard = [
        [
            (
                f"{lang.add_button} {lang.season.lower()}",
                f"manage add season {anime_id} {page}",
            )
        ]
    ]

    seasons = []
    for episode in await Episodes.filter(anime=anime_id):
        if episode.season not in seasons:
            seasons.append(episode.season)

    buttons: List[Tuple] = []
    for season in seasons:
        using = season == SEASON[str(user.id)][str(anime_id)]
        text = ("✅ " if using else "") + str(season)
        data = "noop" if using else f"manage set season {anime_id} {season} {page}"
        buttons.append((text, data))

    if len(buttons) > 0:
        keyboard += array_chunk(buttons, 2)
    keyboard.append([(lang.back_button, f"manage episodes {anime_id} {page}")])

    await callback.edit_message_text(lang.settings_season, reply_markup=ikb(keyboard))


@Amime.on_callback_query(
    filters.regex(r"^manage set season (?P<id>\d+) (?P<season>\d+) (?P<page>\d+)")
)
async def manage_set_season_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    user = callback.from_user

    SEASON[str(user.id)][str(anime_id)] = season

    await manage_season_callback(bot, callback)


@Amime.on_callback_query(
    filters.regex(
        r"^manage del season (?P<id>\d+) (?P<season>\d+) (?P<language>\w+) (?P<page>\d+)"
    )
)
async def manage_del_season_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    language = callback.matches[0]["language"]
    page = int(callback.matches[0]["page"])
    user = callback.from_user
    lang = callback._lang

    keyboard = [
        [
            (
                lang.confirm_button,
                f"manage confirm del season {anime_id} {season} {language} {page}",
            ),
            (lang.cancel_button, f"manage episodes {anime_id} {page}"),
        ]
    ]

    await callback.edit_message_text(
        lang.confirm,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(
        r"^manage confirm del season (?P<id>\d+) (?P<season>\d+) (?P<language>\w+) (?P<page>\d+)"
    )
)
async def manage_confirm_del_season_callback(bot: Amime, callback: CallbackQuery):
    anime_id = int(callback.matches[0]["id"])
    season = int(callback.matches[0]["season"])
    language = callback.matches[0]["language"]
    user = callback.from_user

    if season > 0:
        SEASON[str(user.id)][str(anime_id)] = SEASON[str(user.id)][str(anime_id)] - 1

    for episode in await Episodes.filter(
        anime=anime_id, season=season, language=language
    ):
        await episode.delete()

    await manage_episodes_callback(bot, callback)
