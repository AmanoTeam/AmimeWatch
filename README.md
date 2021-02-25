# AmimeWatch

> A bot dedicated to Otakus made in Python using the [Pyrogram](//github.com/pyrogram/pyrogram) framework.

This repository contains the source code of [@AmimeWatchBot](//t.me/amimewatchbot) and the instructions for running a
copy yourself.

## Requirements

- Python 3.6 or higher.
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