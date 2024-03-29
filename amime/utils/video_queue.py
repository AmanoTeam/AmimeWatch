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
import random
import re
import shutil
from typing import Union

import anilist
from pyrogram.types import Document, Video

from amime.config import CHATS
from amime.database import Episodes


class VideoQueue(object):
    def __init__(self, bot, loop):
        self.bot = bot
        self.loop = loop
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
            future = self.loop.run_in_executor(
                pool, asyncio.ensure_future(self.next()), id
            )
            await asyncio.gather(future, return_exceptions=True)

    async def next(self):
        self.is_running = True

        item = self.queue.get_nowait()
        id, video = item.values()

        directory = f"./downloads/{random.randint(0, 9999)}/"
        while os.path.exists(directory):
            directory = f"./downloads/{random.randint(0, 9999)}/"

        episode = await Episodes.get_or_none(id=id)

        if episode is not None:
            try:
                path = await self.bot.download_media(video, file_name=directory)
                attempts = 0
                while not bool(path):
                    attempts += 1
                    if attempts >= 3:
                        text = "<b>Error processing an episode</b>\n"
                        text += "\n<b>Anime</b>:"
                        text += f"\n    <b>ID</b>: <code>{episode.anime}</code>"
                        text += "\n\n<b>Episode</b>:"
                        if episode.season > 0:
                            text += (
                                f"\n    <b>Season</b>: <code>{episode.season}</code>"
                            )
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

                    path = await self.bot.download_media(
                        video, file_name=directory + video.file_name
                    )

                extension = os.path.splitext(path)[1][1:].strip()

                anime = await anilist.AsyncClient().get(episode.anime, "anime")
                while anime is None:
                    anime = await anilist.AsyncClient().get(episode.anime, "anime")
                    await asyncio.sleep(5)

                codec = None
                softsubbed = False

                proc = await asyncio.create_subprocess_shell(
                    f'ffmpeg -i "{path}" -hide_banner',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                stdout = (await proc.communicate())[0]

                lines = stdout.decode().lower().splitlines()
                for line in lines:
                    if (time := re.search(r"duration: (\d+):(\d+):(\d+)", line)) :
                        hours, minutes, seconds = time.groups()
                        duration = 0
                        duration += int(hours) * 60 * 60
                        duration += int(minutes) * 60
                        duration += int(seconds)
                        video.duration = duration
                    if (resolution := re.search(r", (\d+)x(\d+) \[", line)) :
                        width, height = resolution.groups()
                        video.width = int(width)
                        video.height = int(height)
                    if (codec := re.search(r"video: (\w+)", line)) :
                        codec = codec.group(1)
                    if re.search(r"\((\w+)\): subtitle: (\w+)", line):
                        softsubbed = True

                if isinstance(video, Document):
                    if extension == "mkv":
                        new_path = path.replace(".mkv", ".mp4")
                        crf = "-crf 18 " if codec == "hevc" else ""
                        if softsubbed:
                            bitrate = (
                                "2M"
                                if (video.width >= 1920 and video.height >= 1080)
                                else "950k"
                                if (video.width >= 1280 and video.height >= 720)
                                else "550k"
                            )
                            proc = await asyncio.create_subprocess_shell(
                                f'ffmpeg -i "{path}" -vf subtitles="{path}":si=0:force_style="FontName=Trebuchet MS Bold,Fontsize=24" -c:v libx264 {crf}-pix_fmt yuv420p -b:v {bitrate} -c:a aac -map 0:v -map 0:a:0 "{new_path}" -y',
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.STDOUT,
                            )
                        else:
                            proc = await asyncio.create_subprocess_shell(
                                f'ffmpeg -i "{path}" -c copy {crf}"{new_path}" -y',
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.STDOUT,
                            )
                        await proc.communicate()

                        os.remove(path)
                        path = new_path
                        extension = "mp4"

                thumb = path.replace(f".{extension}", ".jpg")
                proc = await asyncio.create_subprocess_shell(
                    f'ffmpeg -ss 00:00:20 -i "{path}" -vf scale=320:-1 -vframes 1 -q:v 2 "{thumb}" -y',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                await proc.communicate()

                if not os.path.exists(thumb):
                    thumb = (
                        await self.bot.download_media(video.thumbs[0])
                        if bool(video.thumbs) and len(video.thumbs) > 0
                        else None
                    )

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
                duration = video.duration // 60

                episode.update_from_dict(
                    {"file_id": video.file_id, "duration": duration}
                )
                await episode.save()

                os.remove(thumb)
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
            finally:
                shutil.rmtree(f"amime/{directory}", ignore_errors=True)

        if self.queue.empty() is False:
            await self.next()
            return

        self.is_running = False

    def running(self) -> bool:
        return self.is_running
