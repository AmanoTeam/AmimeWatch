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

import datetime
import traceback

from pyrogram import Client

from .. import log


async def save_in_telegram(bot: Client):
    date = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

    log.warning("Saving the database in Telegram...")

    try:
        if await bot.send_document(
            bot.backup_chat.id,
            "amime/database/database.sqlite",
            caption=f"<b>Database BACKUP</b>\n\n<b>Date</b>: <code>{date}</code>",
        ):
            log.warning("Database saved in Telegram successfully!")
        else:
            log.warning("It was not possible to save the database in Telegram.")
    except:
        log.error("Error saving the database in Telegram.")
        traceback.print_exc()
