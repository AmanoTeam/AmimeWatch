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
import datetime
import logging

import aiocron
import pyromod.listen
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.types import User

from amime.config import SUDO_USERS
from amime.utils import (
    backup,
    day_releases,
    filters,
    langs,
    modules,
    scrapper,
    video_queue,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)

# To avoid some annoying log
logging.getLogger("pyrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Amime(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name,
            config_file=f"{name}.ini",
            parse_mode="html",
            workers=24,
            workdir=".",
            sleep_threshold=180,
        )

        self.sudos = SUDO_USERS

        self.start_datetime = datetime.datetime.now().replace(
            tzinfo=datetime.timezone.utc
        )

    async def start(self):
        await super().start()

        self.me = await self.get_me()
        logger.info(
            "AmimeWatch running with Pyrogram v%s (Layer %s) started on @%s. Hi.",
            __version__,
            layer,
            self.me.username,
        )

        loop = asyncio.get_event_loop()

        langs.load()
        modules.load(self)
        self.video_queue = video_queue.VideoQueue(self, loop)
        self.scrapper = scrapper.Scrapper()

        self.day_releases = None

        aiocron.crontab("0 * * * *", func=backup.save, args=(self,), start=True)
        aiocron.crontab(
            "*/10 * * * *", func=day_releases.reload, args=(self,), start=True
        )

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.workers - 4)
        future = loop.run_in_executor(
            pool, asyncio.ensure_future(day_releases.load(self))
        )
        await asyncio.gather(future, return_exceptions=True)

    async def stop(self, *args):
        await super().stop(*args)
        logger.warning("AmimeWatch stopped. Bye.")

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudos
