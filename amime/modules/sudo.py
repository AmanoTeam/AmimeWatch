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
import io
import os
import sys
import traceback
from typing import Dict

import meval
from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.utils import modules


@Amime.on_message(filters.cmd(r"up(grad|dat)e$") & filters.sudo)
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
            for c_hash, commit in commits.items():
                changelog += f"  - [<code>{c_hash[:7]}</code>] {commit['title']}\n"
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


@Amime.on_callback_query(filters.regex(r"^upgrade$") & filters.sudo)
async def upgrade_callback(bot: Amime, callback: CallbackQuery):
    await callback.edit_message_reply_markup({})
    sent = await callback.message.reply_text("Upgrading...")

    proc = await asyncio.create_subprocess_shell(
        "git reset --hard origin/main",
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


@Amime.on_message(filters.cmd("(sh(eel)?|term(inal)?) ") & filters.sudo)
async def terminal_message(bot: Amime, message: Message):
    command = message.text.split()[0]
    code = message.text[len(command) + 1 :]
    sent = await message.reply_text("Running...")

    proc = await asyncio.create_subprocess_shell(
        code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0]

    lines = stdout.decode().splitlines()
    output = "".join(f"<code>{line}</code>\n" for line in lines)
    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    if len(output) > 0:
        if len(output) > (4096 - len(output_message)):
            document = io.BytesIO(
                (output.replace("<code>", "").replace("</code>", "")).encode()
            )
            document.name = "output.txt"
            await bot.send_document(chat_id=message.chat.id, document=document)
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"

    await sent.edit_text(output_message)


@Amime.on_message(filters.cmd("ev(al)? ") & filters.sudo)
async def eval_message(bot: Amime, message: Message):
    command = message.text.split()[0]
    eval_code = message.text[len(command) + 1 :]
    sent = await message.reply_text("Running...")

    try:
        stdout = await meval.meval(eval_code, globals(), **locals())
    except BaseException:
        error = traceback.format_exc()
        await sent.edit_text(
            f"An error occurred while running the code:\n<code>{error}</code>"
        )
        return

    output_message = f"<b>Input\n&gt;</b> <code>{eval_code}</code>\n\n"

    if stdout is not None:
        lines = str(stdout).splitlines()
        output = "".join(f"<code>{line}</code>\n" for line in lines)

        if len(output) > 0:
            if len(output) > (4096 - len(output_message)):
                document = io.BytesIO(
                    (output.replace("<code>", "").replace("</code>", "")).encode()
                )
                document.name = "output.txt"
                await bot.send_document(chat_id=message.chat.id, document=document)
            else:
                output_message += f"<b>Output\n&gt;</b> {output}"

    await sent.edit_text(output_message)


@Amime.on_message(filters.cmd("ex(ec(ute)?)? ") & filters.sudo)
async def execute_message(bot: Amime, message: Message):
    command = message.text.split()[0]
    code = message.text[len(command) + 1 :]
    sent = await message.reply_text("Running...")

    function = "async def _aexec_(bot: Amime, message: Message):"
    for line in code.splitlines():
        function += f"\n    {line}"
    exec(function)

    try:
        stdout = await locals()["_aexec_"](bot, message)
    except BaseException:
        error = traceback.format_exc()
        await sent.edit_text(
            f"An error occurred while running the code:\n<code>{error}</code>"
        )
        return

    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"

    if stdout is not None:
        lines = str(stdout).splitlines()
        output = "".join(f"<code>{line}</code>\n" for line in lines)

        if len(output) > 0:
            if len(output) > (4096 - len(output_message)):
                document = io.BytesIO(
                    (output.replace("<code>", "").replace("</code>", "")).encode()
                )
                document.name = "output.txt"
                await bot.send_document(chat_id=message.chat.id, document=document)
            else:
                output_message += f"<b>Output\n&gt;</b> {output}"

    await sent.edit_text(output_message)


@Amime.on_message(filters.cmd(r"reload$") & filters.sudo)
async def reload_message(bot: Amime, message: Message):
    sent = await message.reply_text("Reloading modules...")
    first = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    modules.reload(bot)
    second = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    await sent.edit_text(
        f"Modules reloaded in <code>{(second - first).microseconds / 1000}ms</code>."
    )
