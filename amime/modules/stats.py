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

import datetime
import os
import platform
import shutil

import humanize
import psutil
from pyrogram import filters
from pyrogram.types import Message

from amime.amime import Amime
from amime.database import (
    Chats,
    Collaborators,
    Episodes,
    Favorites,
    Reports,
    Requests,
    Users,
    Viewed,
    Watched,
)


@Amime.on_message(filters.cmd(r"stats$") & (filters.collaborator | filters.sudo))
async def stats_view(bot: Amime, message: Message):
    lang = message._lang

    text = "<b>General statistics</b>"
    text += "\n    <b>Database</b>:"
    text += f"\n        <b>Size</b>: <code>{humanize.naturalsize(os.stat('amime/database/database.sqlite').st_size, binary=True)}</code>"
    disk = shutil.disk_usage("/")
    text += f"\n        <b>Free</b>: <code>{humanize.naturalsize(disk[2], binary=True)}</code>"
    text += "\n    <b>Episodes</b>:"
    episodes = await Episodes.all()
    text += f"\n        <b>Total</b>: <code>{len(episodes)}</code>"
    for language in lang.strings.keys():
        episodes = await Episodes.filter(language=language)
        text += f"\n        <b>{language.upper()}</b>: <code>{len(episodes)}</code>"
    favorites = await Favorites.all()
    text += f"\n        <b>Favorited</b>: <code>{len(favorites)}</code>"
    reports = await Reports.all()
    text += f"\n        <b>Reported</b>: <code>{len(reports)}</code>"
    viewed = await Viewed.all()
    text += f"\n        <b>Viewed</b>: <code>{len(viewed)}</code>"
    watched = await Watched.all()
    text += f"\n        <b>Watched</b>: <code>{len(watched)}</code>"
    requests = await Requests.all()
    requests_doned = [*filter(lambda request: request.done is True, requests)]
    text += f"\n        <b>Requests doned</b>: <code>{len(requests_doned)}</code>"
    requests_undoned = [*filter(lambda request: request.done is False, requests)]
    text += f"\n        <b>Requests undoned</b>: <code>{len(requests_undoned)}</code>"
    text += "\n    <b>Collaborators</b>:"
    collaborators = await Collaborators.all()
    text += f"\n        <b>Total</b>: <code>{len(collaborators)}</code>"
    for language in lang.strings.keys():
        collaborators = await Collaborators.filter(language=language)
        text += (
            f"\n        <b>{language.upper()}</b>: <code>{len(collaborators)}</code>"
        )
    text += "\n    <b>Chats</b>:"
    chats = await Chats.all()
    text += f"\n        <b>Total</b>: <code>{len(chats)}</code>"
    for language in lang.strings.keys():
        chats = await Chats.filter(language=language)
        text += f"\n        <b>{language.upper()}</b>: <code>{len(chats)}</code>"
    text += "\n    <b>Users</b>:"
    users = await Users.all()
    text += f"\n        <b>Total</b>: <code>{len(users)}</code>"
    for language in lang.strings.keys():
        users = await Users.filter(language_bot=language)
        text += f"\n        <b>{language.upper()}</b>: <code>{len(users)}</code>"
    text += f"\n    <b>Loaded languages</b>: <code>{len(lang.strings.keys())}</code>"

    text += "\n\n<b>System</b>"
    uname = platform.uname()
    text += f"\n    <b>OS</b>: <code>{uname.system}</code>"
    text += f"\n    <b>Node</b>: <code>{uname.node}</code>"
    text += f"\n    <b>Kernel</b>: <code>{uname.release}</code>"
    text += f"\n    <b>Architecture</b>: <code>{uname.machine}</code>"
    memory = psutil.virtual_memory()
    text += f"\n    <b>Memory</b>: <code>{humanize.naturalsize(memory.used, binary=True)}/{humanize.naturalsize(memory.total, binary=True)}</code>"
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    date = now - bot.start_datetime
    text += f"\n    <b>UPTime</b>: <code>{humanize.precisedelta(date)}</code>"

    await message.reply_text(text)


@Amime.on_message(filters.cmd(r"today$"))
async def today_releases_view(bot: Amime, message: Message):
    lang = message._lang

    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    text = lang.day_releases_text(date=now.strftime("%H:%M:%S"))

    animes = bot.day_releases

    keys = sorted([*animes.keys()])
    for key in keys:
        value = animes[key]
        if value is not None:
            text += f"\n<a href='https://t.me/{bot.me.username}/?start=anime_{key}'>{key}</a> - <b>{value[0]}</b> (<i>{value[1]}</i>) - <code>{value[2].strftime('%H:%M:%S')}</code>"

    await message.reply_text(text, disable_web_page_preview=True)
