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
import datetime
import logging
import re

import anilist
from pyrogram import filters
from pyrogram.errors import ListenerCanceled, QueryIdInvalid
from pyrogram.types import (
    CallbackQuery,
    Document,
    InputMediaPhoto,
    InputMediaVideo,
    Video,
)
from pyromod.helpers import array_chunk, ikb
from pyromod.nav import Pagination

from amime.amime import Amime
from amime.database import Episodes, Notifications

logger = logging.getLogger(__name__)


EPISODES = {}
VIDEOS = {}


@Amime.on_callback_query(filters.regex(r"^manage anime (\d+) (\d+) (\d+) (\w+) (\d+)"))
async def anime_manage(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    subtitled = bool(int(callback.matches[0].group(3)))
    language = callback.matches[0].group(4)
    page = int(callback.matches[0].group(5))

    if str(user.id) in VIDEOS.keys() and str(anime_id) in VIDEOS[str(user.id)].keys():
        chat.cancel_listener()
        del VIDEOS[str(user.id)][str(anime_id)]

    buttons = [
        (
            f"{lang.language_button}: {lang.strings[language]['LANGUAGE_NAME']}",
            f"manage anime language {anime_id} {season} {language} {page}",
        ),
        (
            f"{lang.season_button}: {season}",
            f"manage anime season {anime_id} {season} {int(subtitled)} {language} {page}",
        ),
        (
            f"{lang.subtitled_button}: {lang.yes if subtitled else lang.no}",
            f"manage anime {anime_id} {season} {int(not subtitled)} {language} {page}",
        ),
        (
            lang.add_button,
            f"manage episode {anime_id} {season} -1 {int(subtitled)} {language} {page}",
        ),
    ]

    episodes = await Episodes.filter(
        anime=anime_id, season=season, language=language, subtitled=subtitled
    )
    episodes = sorted(episodes, key=lambda episode: episode.number)

    if len(episodes) >= 2:
        buttons.append(
            (
                lang.del_season_button,
                f"manage episode delete {anime_id} {season} -1 {int(subtitled)} {language} {page}",
            )
        )
    else:
        if page > 0:
            page -= 1
            matches = re.search(
                r"(\d+) (\d+) (\d+) (\w+) (\d+)",
                f"{anime_id} {season} {int(subtitled)} {language} {page}",
            )
            callback.matches = [matches]
            await anime_manage(bot, callback)
            return

    buttons.append(
        (
            lang.add_in_batch_button,
            f"manage episode batch {anime_id} {season} {int(subtitled)} {language} {page}",
        )
    )

    notifications = await Notifications.filter(
        item=anime_id,
        type="anime",
        language=language,
    )
    if len(notifications) > 0:
        buttons.append(
            (
                lang.notify_users_button,
                f"notify episodes {anime_id} {season} {language} {page}",
            )
        )

    keyboard = array_chunk(buttons, 2)

    layout = Pagination(
        episodes,
        item_data=lambda i, pg: f"manage episode {i.anime} {i.season} {i.number} {int(subtitled)} {language} {pg}",
        item_title=lambda i, pg: f"📝 {i.number}",
        page_data=lambda pg: f"manage anime {anime_id} {season} {int(subtitled)} {language} {pg}",
    )

    lines = layout.create(page, lines=5, columns=3)

    if len(lines) > 0:
        keyboard += lines

    keyboard.append([(lang.back_button, f"anime {anime_id}")])

    if bool(message.photo):
        await message.edit_text(
            lang.manage_anime_text,
            reply_markup=ikb(keyboard),
        )
    else:
        await callback.edit_message_media(
            InputMediaPhoto(
                f"https://img.anili.st/media/{anime_id}",
                caption=lang.manage_anime_text,
            ),
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(
    filters.regex(r"^manage anime season (\d+) (\d+) (\d+) (\w+) (\d+)")
)
async def anime_season(bot: Amime, callback: CallbackQuery):
    message = callback.message
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    subtitled = bool(int(callback.matches[0].group(3)))
    language = callback.matches[0].group(4)
    page = int(callback.matches[0].group(5))

    episodes = await Episodes.filter(
        anime=anime_id, language=language, subtitled=subtitled
    )
    episodes = sorted(episodes, key=lambda episode: episode.number)

    seasons = [0]
    for episode in episodes:
        if episode.season not in seasons:
            seasons.append(episode.season)

    seasons.sort()
    if season not in seasons:
        seasons.append(season)

    keyboard = [
        [
            (
                lang.add_button,
                f"manage anime {anime_id} {seasons[-1] + 1} {int(subtitled)} {language} 1",
            )
        ],
    ]

    buttons = []
    for _season in seasons:
        text = ("✅" if _season == season else "") + f" {_season}"
        data = (
            "noop"
            if _season == season
            else f"manage anime season {anime_id} {_season} {int(subtitled)} {language} 1"
        )
        buttons.append((text, data))

    keyboard += array_chunk(buttons, 2)

    keyboard.append(
        [
            (
                lang.back_button,
                f"manage anime {anime_id} {season} {int(subtitled)} {language} {page}",
            )
        ]
    )

    await message.edit_text(
        lang.season_text,
        reply_markup=ikb(keyboard),
    )


@Amime.on_callback_query(
    filters.regex(r"^manage episode (\d+) (\d+) (\-?\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    number = int(callback.matches[0].group(3))
    subtitled = bool(int(callback.matches[0].group(4)))
    language = callback.matches[0].group(5)
    page = int(callback.matches[0].group(6))

    if str(user.id) not in EPISODES.keys():
        EPISODES[str(user.id)] = {}
    if str(anime_id) not in EPISODES[str(user.id)].keys():
        EPISODES[str(user.id)][str(anime_id)] = {}

    chat.cancel_listener()

    episode = EPISODES[str(user.id)][str(anime_id)]

    episode_db = await Episodes.get_or_none(
        anime=anime_id,
        season=season,
        number=number,
        language=language,
        subtitled=subtitled,
    )
    if episode_db is not None:
        if not ("id" in episode.keys() and episode["id"] == episode_db.id):
            episode["id"] = episode_db.id
            episode["video"] = episode_db.file_id
            episode["name"] = episode_db.name
            episode["notes"] = episode_db.notes
            episode["duration"] = episode_db.duration
            episode["unified_until"] = episode_db.unified_until

            EPISODES[str(user.id)][str(anime_id)] = episode
    elif number == -1:
        EPISODES[str(user.id)][str(anime_id)] = {}
        episode = EPISODES[str(user.id)][str(anime_id)]

        episodes = await Episodes.filter(
            anime=anime_id,
            season=season,
            language=language,
            subtitled=subtitled,
        )
        episodes = sorted(episodes, key=lambda episode: episode.number)
        if len(episodes) > 0:
            number = episodes[-1].number + 1
        else:
            number = 1

    episode["subtitled"] = subtitled

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        if anime is None:
            return

        logger.debug(
            "%s is editing/adding episode %s of the anime %s (%s)",
            user.first_name,
            number,
            anime_id,
            language,
        )

        text = lang.manage_episode_text
        text += f"\n<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"

        buttons = []

        if "name" in episode.keys() and len(episode["name"]) > 0:
            text += f"\n<b>{lang.name}</b>: <code>{episode['name']}</code>"
            buttons.append(
                (
                    f"✏️ {lang.name}",
                    f"manage episode edit name {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )
        else:
            buttons.append(
                (
                    f"➕ {lang.name}",
                    f"manage episode edit name {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        if season > 0:
            text += f"\n<b>{lang.season}</b>: <code>{season}</code>"

        if number != -1:
            episode_number = str(number)
            if "unified_until" in episode.keys() and int(episode["unified_until"]) > 0:
                episode_number += f"-{episode['unified_until']}"
            text += f"\n<b>{lang.episode}</b>: <code>{episode_number}</code>"
            buttons.append(
                (
                    f"✏️ {lang.episode}",
                    f"manage episode edit number {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )
        else:
            buttons.append(
                (
                    f"➕ {lang.episode}",
                    f"manage episode edit number {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        if "video" in episode.keys():
            buttons.append(
                (
                    f"✏️ {lang.video}",
                    f"manage episode edit video {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )
        else:
            buttons.append(
                (
                    f"➕ {lang.video}",
                    f"manage episode edit video {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        if "duration" in episode.keys():
            text += f"\n<b>{lang.duration}</b>: <code>{episode['duration']}m</code>"
            buttons.append(
                (
                    f"✏️ {lang.duration}",
                    f"manage episode edit duration {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )
        else:
            buttons.append(
                (
                    f"➕ {lang.duration}",
                    f"manage episode edit duration {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        text += f"\n<b>{lang.language}</b>: <code>{lang.strings[language]['LANGUAGE_NAME']}</code>"

        if "notes" in episode.keys() and len(episode["notes"]) > 0:
            text += f"\n<b>{lang.notes}</b>: <i>{episode['notes']}</i>"
            buttons.append(
                (
                    f"✏️ {lang.notes}",
                    f"manage episode edit notes {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )
        else:
            buttons.append(
                (
                    f"➕ {lang.notes}",
                    f"manage episode edit notes {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        keyboard = array_chunk(buttons, 2)

        buttons = []
        if number != -1 and "video" in episode.keys():
            episode["number"] = number
            buttons.append(
                (
                    lang.confirm_button,
                    f"manage episode save {anime_id} {season} {int(subtitled)} {language} {page}",
                )
            )

        if "id" in episode.keys():
            buttons.append(
                (
                    lang.del_button,
                    f"manage episode delete {anime_id} {season} {number} {int(subtitled)} {language} {page}",
                )
            )

        buttons.append(
            (
                lang.back_button,
                f"manage anime {anime_id} {season} {int(subtitled)} {language} {page}",
            )
        )

        keyboard += array_chunk(buttons, 2)

        if "video" in episode.keys():
            file_id = False
            if isinstance(episode["video"], str) and len(episode["video"]) > 0:
                file_id = episode["video"]
            elif isinstance(episode["video"], Video):
                file_id = episode["video"].file_id

            if file_id is not False:
                try:
                    await callback.edit_message_media(
                        InputMediaVideo(
                            file_id,
                            caption=text,
                        ),
                        reply_markup=ikb(keyboard),
                    )
                    return
                except BaseException:
                    pass
        await callback.edit_message_media(
            InputMediaPhoto(
                f"https://img.anili.st/media/{anime_id}",
                caption=text,
            ),
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(
    filters.regex(r"^manage episode edit (\w+) (\d+) (\d+) (\-?\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode_edit(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    item = callback.matches[0].group(1)
    anime_id = int(callback.matches[0].group(2))
    season = int(callback.matches[0].group(3))
    number = int(callback.matches[0].group(4))
    subtitled = bool(int(callback.matches[0].group(5)))
    language = callback.matches[0].group(6)
    page = int(callback.matches[0].group(7))

    episode = EPISODES[str(user.id)][str(anime_id)]

    keyboard = [
        [
            (
                lang.cancel_button,
                f"manage episode {anime_id} {season} {number} {int(subtitled)} {language} {page}",
            ),
        ],
    ]

    await message.edit_text(
        lang.send_me_the_item_text(item=lang.strings[lang.code][item].lower()),
        reply_markup=ikb(keyboard),
    )

    answer = None

    if item == "video":
        while True:
            try:
                answer = await chat.listen(filters.video | filters.document)
            except ListenerCanceled:
                return

            if bool(answer.video):
                duration = answer.video.duration
                if duration <= 30:
                    try:
                        await callback.answer(
                            lang.very_short_video_alert, show_alert=True
                        )
                        continue
                    except QueryIdInvalid:
                        sent = await answer.reply_text(lang.very_short_video_alert)
                        await asyncio.sleep(3)
                        await sent.delete()
                        continue

                episode["video"] = answer.video
                episode["duration"] = duration // 60
            elif bool(answer.document):
                episode["video"] = answer.document

            if bool(answer.forward_from) and answer.forward_from.id == bot.me.id:
                episode["update_video"] = False
            else:
                episode["update_video"] = True
            break
    else:
        if item == "number":
            while True:
                try:
                    answer = await chat.listen(filters.text)
                except ListenerCanceled:
                    return

                ep = answer.text.split("-")
                if not int(ep[0]) == number:
                    number = ep[0]

                    if len(ep) > 1:
                        episode["unified_until"] = ep[1]
                    else:
                        episode["unified_until"] = "0"

                    answers = []

                    if bool(
                        await Episodes.get_or_none(
                            anime=anime_id,
                            season=season,
                            number=number,
                            language=language,
                        )
                    ):
                        try:
                            await callback.answer(
                                lang.episode_already_exists_alert, show_alert=True
                            )
                        except QueryIdInvalid:
                            sent = await answer.reply_text(
                                lang.episode_already_exists_alert
                            )
                            await asycio.sleep(3)
                            await sent.delete()
                        finally:
                            continue

                        number = answer.text
                        answers.append(answer)

                    for _answer in answers:
                        try:
                            await _answer.delete()
                            await asyncio.sleep(1)
                        except BaseException:
                            pass
                break
        else:
            try:
                answer = await chat.listen(filters.text)
            except ListenerCanceled:
                return

            episode[item] = answer.text

    try:
        await answer.delete()
    except BaseException:
        pass

    EPISODES[str(user.id)][str(anime_id)] = episode

    matches = re.search(
        r"(\d+) (\d+) (\-?\d+) (\d+) (\w+) (\d+)",
        f"{anime_id} {season} {number} {int(subtitled)} {language} {page}",
    )
    callback.matches = [matches]

    await anime_episode(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"^manage episode save (\d+) (\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode_save(bot: Amime, callback: CallbackQuery):
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    subtitled = bool(int(callback.matches[0].group(3)))
    language = callback.matches[0].group(4)
    page = int(callback.matches[0].group(5))

    episode = EPISODES[str(user.id)][str(anime_id)]

    logger.debug(
        "%s is edited/saved episode %s of the anime %s (%s)",
        user.first_name,
        episode["number"],
        anime_id,
        language,
    )

    episode["anime"] = anime_id
    episode["season"] = season
    episode["language"] = language
    episode["added_by"] = str(user.id)

    id = -1
    if "id" in episode.keys():
        id = episode["id"]

    video = episode["video"]

    if isinstance(episode["video"], Document):
        episode["file_id"] = ""
    elif isinstance(episode["video"], Video):
        episode["file_id"] = episode["video"].file_id
    del episode["video"]

    number = episode["number"]

    if "id" in episode.keys():
        episode_db = await Episodes.get(id=episode["id"])
        del episode["id"]
        episode_db.update_from_dict(episode)
        await episode_db.save()
    else:
        episode_db = await Episodes.create(**episode)
        id = episode_db.id

        now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        await Notifications.create(
            item=anime_id,
            type="anime",
            season=season,
            number=number,
            language=language,
            datetime=now_date,
        )

    if "update_video" in episode.keys() and episode["update_video"] is True:
        await bot.video_queue.add(id, video)

    await callback.answer(lang.confirm_save_episode_alert, show_alert=True)

    matches = re.search(
        r"(\d+) (\d+) (\d+) (\w+) (\d+)",
        f"{anime_id} {season} {int(subtitled)} {language} {page}",
    )
    callback.matches = [matches]

    await anime_manage(bot, callback)

    del EPISODES[str(user.id)][str(anime_id)]


@Amime.on_callback_query(
    filters.regex(r"^manage episode delete (\d+) (\d+) (\-?\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode_delete(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    number = int(callback.matches[0].group(3))
    subtitled = bool(int(callback.matches[0].group(4)))
    language = callback.matches[0].group(5)
    page = int(callback.matches[0].group(6))

    episodes = []

    if number == -1:
        keyboard = [
            [
                (
                    lang.confirm_button,
                    f"manage episode delete {anime_id} {season} -2 {int(subtitled)} {language} {page}",
                ),
                (
                    lang.cancel_button,
                    f"manage anime {anime_id} {season} {int(subtitled)} {language} {page}",
                ),
            ],
        ]

        await message.edit_text(
            lang.confirm_text,
            reply_markup=ikb(keyboard),
        )
        return
    elif number == -2:
        episodes = await Episodes.filter(
            anime=anime_id,
            season=season,
            language=language,
            subtitled=subtitled,
        )

        logger.debug(
            "%s deleted season %s of the anime %s (%s)",
            user.first_name,
            season,
            anime_id,
            language,
        )
    else:
        episodes = [
            await Episodes.get(
                anime=anime_id,
                season=season,
                number=number,
                language=language,
                subtitled=subtitled,
            )
        ]

        logger.debug(
            "%s deleted episode %s of the anime %s (%s)",
            user.first_name,
            number,
            anime_id,
            language,
        )

    for episode in episodes:
        notification = await Notifications.get_or_none(
            item=anime_id, type="anime", season=season, number=number, language=language
        )
        if notification is not None:
            await notification.delete()
        await episode.delete()

    await callback.answer(lang.confirm_delete_episode_alert, show_alert=True)

    matches = re.search(
        r"(\d+) (\d+) (\d+) (\w+) (\d+)",
        f"{anime_id} {season} {int(subtitled)} {language} {page}",
    )
    callback.matches = [matches]

    await anime_manage(bot, callback)


@Amime.on_callback_query(
    filters.regex(r"^manage episode batch (\d+) (\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode_batch(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    subtitled = bool(int(callback.matches[0].group(3)))
    language = callback.matches[0].group(4)
    page = int(callback.matches[0].group(5))

    keyboard = [
        [
            (
                lang.confirm_button,
                f"manage episode batch confirm {anime_id} {season} {int(subtitled)} {language} {page}",
            ),
            (
                lang.back_button,
                f"manage anime {anime_id} {season} {int(subtitled)} {language} {page}",
            ),
        ]
    ]

    await message.edit_text(
        lang.add_in_batch_text(
            confirm_button=lang.confirm_button,
        ),
        reply_markup=ikb(keyboard),
    )

    if str(user.id) not in VIDEOS.keys():
        VIDEOS[str(user.id)] = {}
    if str(anime_id) not in VIDEOS[str(user.id)].keys():
        VIDEOS[str(user.id)][str(anime_id)] = []

    while True:
        if len(VIDEOS[str(user.id)][str(anime_id)]) >= 30:
            await anime_episode_batch_confirm(bot, callback)
            break

        try:
            msg = await chat.listen(filters.video)
        except ListenerCanceled:
            break

        if bool(msg.video):
            VIDEOS[str(user.id)][str(anime_id)].append(msg)


@Amime.on_callback_query(
    filters.regex(r"^manage episode batch confirm (\d+) (\d+) (\d+) (\w+) (\d+)")
)
async def anime_episode_batch_confirm(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    season = int(callback.matches[0].group(2))
    subtitled = bool(int(callback.matches[0].group(3)))
    language = callback.matches[0].group(4)
    page = int(callback.matches[0].group(5))

    chat.cancel_listener()

    videos = VIDEOS[str(user.id)][str(anime_id)]

    if len(videos) == 1:
        await callback.answer(lang.only_1_episode_not_allowed_alert, show_alert=True)

        del VIDEOS[str(user.id)][str(anime_id)]

        await anime_manage(bot, callback)
        return
    elif len(videos) > 0:
        await message.edit_text(
            lang.add_in_batch_videos_text(
                count=len(videos),
            ),
        )
    else:
        await message.edit_text(
            lang.no_found_episodes_text,
            reply_markup=ikb(
                [
                    [
                        (
                            lang.back_button,
                            f"manage episode batch {anime_id} {season} {int(subtitled)} {language} {page}",
                        )
                    ]
                ]
            ),
        )
        return

    numbers_added = []
    for msg in videos:
        video, caption = msg.video, msg.caption

        if len(caption) == 0:
            continue

        name, number, unified_until = (None,) * 3

        query = caption.split("|")

        query[0] = query[0].split()[0]
        if "-" in query[0]:
            number, unified_until = query[0].split("-")
        elif query[0].isdecimal():
            number = query[0]

        if number is None:
            continue

        if number in numbers_added or bool(
            await Episodes.get_or_none(
                anime=anime_id,
                season=season,
                number=number,
                language=language,
                subtitled=subtitled,
            )
        ):
            continue
        numbers_added.append(number)

        if len(query) > 1:
            name = query[1].strip()

        episode = await Episodes.create(
            anime=anime_id,
            file_id=video.file_id,
            name=name or "",
            added_by=user.id,
            season=season,
            number=number,
            duration=video.duration // 60,
            language=language,
            unified_until=unified_until or "0",
            subtitled=subtitled,
        )
        video_id = episode.id

        now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        await Notifications.create(
            item=anime_id,
            type="anime",
            season=season,
            number=number,
            language=language,
            datetime=now_date,
        )

        await bot.video_queue.add(video_id, video)

        try:
            await msg.delete()
        except BaseException:
            pass

    logger.debug(
        "%s added %s episodes on the anime %s (%s)",
        user.first_name,
        len(videos),
        anime_id,
        language,
    )

    del VIDEOS[str(user.id)][str(anime_id)]

    await callback.answer(lang.confirm_save_episode_alert, show_alert=True)

    await anime_manage(bot, callback)
