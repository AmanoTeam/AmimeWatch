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

import asyncio
import aioschedule as schedule
import pyromod.listen

from datetime import datetime

from pyrogram import Client
from pyrogram import __version__
from pyrogram.raw.all import layer
from pyrogram.types import User

from . import log
from .utils import backup, langs, modules


class Amime(Client):
    SUDO_USERS = [1155717290, 918317361]  # @AndrielFR and @Hitalo
    BACKUP_ID = -1001339690483
    STAFF_ID = -1001382912209
    VIDEOS_ID = -1001343429763
    REQUESTS_ID = -1001176439164
    CHANNEL_ID = -1001354975349

    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name,
            config_file=f"{name}.ini",
            workers=16,
            workdir=".",
        )

        self.sudos = Amime.SUDO_USERS

        self.start_datetime = datetime.utcnow()

    async def start(self):
        await super().start()

        self.me = await self.get_me()
        log.info(
            f"AmimeWatch running with Pyrogram v{__version__} (Layer {layer}) started on @{self.me.username}. Hi."
        )

        langs.load()
        await modules.load(self)

        self.backup_chat = await self.get_chat(Amime.BACKUP_ID)
        self.staff_chat = await self.get_chat(Amime.STAFF_ID)
        self.videos_chat = await self.get_chat(Amime.VIDEOS_ID)
        self.requests_chat = await self.get_chat(Amime.REQUESTS_ID)
        self.channel_id = Amime.CHANNEL_ID

        schedule.every(1).hour.do(backup.save_in_telegram, bot=self)

        while True:
            await schedule.run_pending()
            await asyncio.sleep(0.1)

    async def stop(self, *args):
        await super().stop()
        log.warning("AmimeWatch stopped. Bye.")

    def is_sudo(self, user: User) -> bool:
        return user.id in self.sudos
