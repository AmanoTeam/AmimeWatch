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
import concurrent.futures
import os
from typing import Union

import anilist
import ffmpeg
from pyrogram.types import Document, Video

from amime.config import CHATS
from amime.database import Episodes


class VideoQueue(object):
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.is_running = False

    async def add(self, id: int, video: Union[Document, Video]):
        item = dict(
            id=id,
            video=video,
        )
        self.queue.put_nowait(item)

        if not self.running():
            pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.bot.workers - 4
            )
            future = asyncio.get_event_loop().run_in_executor(
                pool, asyncio.ensure_future(self.next()), id
            )
            await asyncio.gather(future, return_exceptions=True)

    async def next(self):
        self.is_running = True

        item = self.queue.get_nowait()
        id, video = item.values()

        episode = await Episodes.get(id=id)

        if isinstance(video, Video):
            path = await self.bot.download_media(video)
            attempts = 0
            while not bool(path):
                attempts += 1
                if attempts >= 3:
                    text = "<b>Error processing an episode</b>\n"
                    text += "\n<b>Anime</b>:"
                    text += f"\n    <b>ID</b>: <code>{episode.anime}</code>"
                    text += "\n\n<b>Episode</b>:"
                    if episode.season > 0:
                        text += f"\n    <b>Season</b>: <code>{episode.season}</code>"
                    text += f"\n    <b>Number</b>: <code>{episode.number}</code>"
                    text += "\n\n<b>Error</b>:"
                    text += "\n    <b>AttemptsError</b>:"
                    text += "\n        <i>The number of download attempts has been exhausted.</i>"

                    await self.bot.send_message(
                        CHATS["staff"],
                        text,
                    )

                    if self.queue.empty() is False:
                        await self.next()
                    return

                path = await self.bot.download_media(video)

            anime = await anilist.AsyncClient().get(episode.anime, "anime")

            extension = path.split(".")[-1]

            try:
                thumb = path.replace(f".{extension}", ".jpg")
                (
                    ffmpeg.input(path, ss=20.0)
                    .filter("scale", 320, -1)
                    .output(thumb, vframes=1)
                    .overwrite_output()
                    .run()
                )
            except ffmpeg.Error as e:
                thumb = (
                    await self.bot.download_media(video.thumbs[0])
                    if len(video.thumbs) > 0
                    else None
                )

            try:
                video = (
                    await self.bot.send_video(
                        CHATS["videos"],
                        path,
                        f"<b>{anime.title.romaji} </b> - {episode.season} - {episode.number}",
                        duration=video.duration,
                        width=video.width,
                        height=video.height,
                        thumb=thumb,
                        file_name=f"@{self.bot.me.username} - {anime.title.romaji} - {episode.season} - {episode.number}.{extension}",
                        supports_streaming=True,
                    )
                ).video

                episode.update_from_dict({"file_id": video.file_id})
                await episode.save()
            except BaseException as excep:
                text = "<b>Error processing an episode</b>\n"
                text += "\n<b>Anime</b>:"
                text += f"\n    <b>ID</b>: <code>{episode.anime}</code>"
                text += "\n\n<b>Episode</b>:"
                if episode.season > 0:
                    text += f"\n    <b>Season</b>: <code>{episode.season}</code>"
                text += f"\n    <b>Number</b>: <code>{episode.number}</code>"
                text += "\n\n<b>Error</b>:"
                text += f"\n    <b>{excep.__class__.__name__}</b>:"
                text += f"\n        <i>{excep}</i>"

                await self.bot.send_message(
                    CHATS["staff"],
                    text,
                )

            os.remove(path)
            os.remove(thumb)

        if self.queue.empty() is False:
            await self.next()
            return

        self.is_running = False

    def running(self) -> bool:
        return self.is_running
