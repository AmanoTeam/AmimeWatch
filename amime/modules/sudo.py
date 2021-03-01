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
import os
import sys

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb
from typing import Dict

from ..amime import Amime


@Amime.on_message(filters.cmd(r"up(gr|d)a(d|t)e") & filters.sudo)
async def upgrade_message(bot: Amime, message: Message):
    sent = await message.reply_text("Checking for updates...")

    await (await asyncio.create_subprocess_shell("git fetch origin")).communicate()
    proc = await asyncio.create_subprocess_shell(
        "git log HEAD..origin/main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()

    if proc.returncode == 0:
        if len(stdout) > 0:
            changelog = "<b>Changelog</b>:\n"
            commits = parse_commits(stdout)
            for hash, commit in commits.items():
                changelog += f"  - [<code>{hash[:7]}</code>] {commit['title']}\n"
            changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."

            keyboard = [[("🆕 Upgrade", "upgrade")]]
            await sent.edit_text(changelog, reply_markup=ikb(keyboard))
        else:
            await sent.edit_text("There is nothing to update.")
    else:
        error = ""
        lines = stdout.split("\n")
        for line in lines:
            error += f"<code>{line}</code>\n"
        await sent.edit_text(
            f"Update failed (process exited with {proc.returncode}):\n{error}"
        )


def parse_commits(log: str) -> Dict:
    commits: Dict = {}
    last_commit = ""
    lines = log.split("\n")
    for line in lines:
        if line.startswith("commit"):
            last_commit = line.split()[1]
            commits[last_commit] = {}
        if len(line) > 0:
            if line.startswith("    "):
                if "title" in commits[last_commit].keys():
                    commits[last_commit]["message"] = line[4:]
                else:
                    commits[last_commit]["title"] = line[4:]
            else:
                if ":" in line:
                    key, value = line.split(": ")
                    commits[last_commit][key] = value
    return commits


@Amime.on_callback_query(filters.regex(r"^upgrade") & filters.sudo)
async def upgrade_callback(bot: Amime, callback: CallbackQuery):
    await callback.edit_message_reply_markup({})
    sent = await callback.message.reply_text("Upgrading...")

    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()

    if proc.returncode == 0:
        await sent.edit_text("Restarting...")
        args = [sys.executable, "-m", "amime"]
        os.execv(sys.executable, args)
    else:
        error = ""
        lines = stdout.split("\n")
        for line in lines:
            error += f"<code>{line}</code>\n"
        await sent.edit_text(
            f"Update failed (process exited with {proc.returncode}):\n{error}"
        )


@Amime.on_message(filters.cmd(r"re(boot|start)") & filters.sudo)
async def reboot_message(bot: Amime, message: Message):
    await message.reply_text("Restarting...")
    args = [sys.executable, "-m", "amime"]
    os.execv(sys.executable, args)


@Amime.on_message(filters.cmd(r"shutdown") & filters.sudo)
async def shutdown_message(bot: Amime, message: Message):
    await message.reply_text("Turning off...")
    sys.exit(0)
