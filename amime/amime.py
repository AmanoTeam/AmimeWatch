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
import sys

import aioschedule as schedule
import pyromod.listen
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.types import User

from amime.config import SUDO_USERS
from amime.utils import backup, day_releases, filters, langs, modules, video_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)

# To avoid some pyrogram annoying log
logging.getLogger("pyrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Amime(Client):
    def __init__(self, test_mode: bool = False):
        name = self.__class__.__name__.lower()

        super().__init__(
            name,
            config_file=f"{name}.ini",
            parse_mode="html",
            workers=24,
            workdir=".",
            test_mode=test_mode,
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

        langs.load()
        modules.load(self)
        self.video_queue = video_queue.VideoQueue(self)

        self.day_releases = None

        if self.test_mode:
            await asyncio.sleep(10)
            sys.exit(0)
        else:
            await day_releases.load(self)

            schedule.every(1).hour.do(backup.save_in_telegram, bot=self)
            schedule.every(15).minutes.do(day_releases.reload, bot=self)
            schedule.every().day.at("00:00").do(day_releases.load, bot=self)

            while True:
                await schedule.run_pending()
                await asyncio.sleep(1)

    async def stop(self, *args):
        await super().stop(*args)
        logger.warning("AmimeWatch stopped. Bye.")

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudos
