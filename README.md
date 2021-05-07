# AmimeWatch

> A bot dedicated to Otakus made in Python using the [Pyrogram](//github.com/pyrogram/pyrogram) framework.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub contributors](https://img.shields.io/github/contributors/AmanoTeam/AmimeWatch.svg)](https://GitHub.com/AmanoTeam/AmimeWatch/graphs/contributors/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/ce5d204fd63d483894620d7f409f3a1c)](https://www.codacy.com/gh/AmanoTeam/AmimeWatch/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=AmanoTeam/AmimeWatch&amp;utm_campaign=Badge_Grade)

This repository contains the source code of [@AmimeWatchBot](//t.me/amimewatchbot) and the instructions for running a
copy yourself.

## Requirements

- Python 3.8 or higher.
- A [Telegram API key](//docs.pyrogram.org/intro/setup#api-keys).
- A [Telegram bot token](//t.me/botfather).

## Run

1. `git clone https://github.com/AmanoTeam/AmimeWatch`, to download the source code.
2. `cd AmimeWatch`, to enter the directory.
3. `virtualenv venv && . venv/bin/activate` to create and activate a virtual environment.
3. `pip install -Ur requirements.txt`, to install the requirements.
4. Create a new `amime.ini` file, copy-paste the following and replace the values with your own:
   ```ini
   [pyrogram]
   api_id = 12345
   api_hash = 0123456789abcdef0123456789abcdef
   bot_token = 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
5. Run with `python -m amime`.
6. Stop with <kbd>CTRL+C</kbd> and `deactivate` the virtual environment.

## License

MIT © 2021 [AmanoTeam](//github.com/AmanoTeam)