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

import os
import random
import re
import shutil
from typing import Dict, Optional, Union

import async_files
import bs4
import httpx


class Scrapper(object):
    def __init__(self):
        self.sites = [AnimesVision]

    async def get(self, url: str) -> Optional[Union[Dict, str]]:
        for site in self.sites:
            if re.match(site.PATTERN, url):
                site = site(url)
                await site.get()
                return site

        return None


class AnimesVision:
    PATTERN = r"^(?i)https://(?:www\.)?animesvision\.biz/animes/(.*)"

    def __init__(self, url: str):
        self.players = None
        self.url = url

    async def get(self):
        urls: Union[Dict, str] = None

        async with httpx.AsyncClient(http2=True) as client:
            response = await client.get(self.url)
            soup = bs4.BeautifulSoup(response.text, "html.parser")

            watch = soup.find("div", **{"class": "watch"})
            if watch:
                players = await self.get_players(
                    watch.find_all("div", re.compile(r"tab-pane"))
                )
                players["headers"] = response.headers
                players["cookies"] = response.cookies
                urls = players
            else:
                urls = {}

                tab = soup.find("div", **{"class": "tab-content"})
                episodes = tab.find_all("li", **{"class": "ep-item"})
                for episode in episodes:
                    number = int(re.search(r"(\d+)", str(episode.find("a"))).group(1))

                    link = episode.find("a")["href"]
                    response = await client.get(link)
                    soup = bs4.BeautifulSoup(response.text, "html.parser")

                    watch = soup.find("div", **{"class": "watch"})
                    players = await self.get_players(
                        watch.find_all("div", re.compile(r"tab-pane"))
                    )
                    players["headers"] = response.headers
                    players["cookies"] = response.cookies
                    urls[number] = players

        self.players = urls

    async def get_players(self, players) -> Optional[Union[Dict, str]]:
        urls: Union[Dict, str] = None

        if len(players) > 1:
            urls = {}

        for player in players:
            quality: str = player["id"].upper()
            file: str = None

            if quality == "VIP":
                continue

            for line in player:
                if (match := re.search(r"file: '(.+)'", str(line))) :
                    file = match.group(1)

            if isinstance(urls, Dict):
                urls[quality] = file
            else:
                urls = file

        return urls

    async def download(self, quality: str = "HD", number: int = 1) -> Optional[str]:
        if "HD" in self.players.keys() or "SD" in self.players.keys():
            files = self.players
        else:
            if number not in self.players.keys():
                raise ValueError("Episode not found")
            if quality not in self.players[number].keys():
                raise ValueError("Quality not found")
            files = self.players[number]

        files["headers"]["Referer"] = "https://animesvision.biz"

        directory = f"amime/downloads/{random.randint(0, 9999)}/"
        while os.path.exists(directory):
            directory = f"amime/downloads/{random.randint(0, 9999)}/"

        os.makedirs(directory)

        url = files[quality]
        path = os.path.join(directory, os.path.basename(url))

        file_size = 0

        try:
            async with httpx.AsyncClient(http2=True) as client:
                async with client.stream(
                    "GET", url, headers=files["headers"], cookies=files["cookies"]
                ) as response:
                    file_size = int(response.headers["Content-Length"])

                    if response.status_code != 200:
                        return None

                    async with async_files.FileIO(path, "wb") as file:
                        async for chunk in response.aiter_bytes():
                            await file.write(chunk)

                        await file.close()

                await client.aclose()
        except (httpx.ConnectError, httpx.RemoteProtocolError):
            shutil.rmtree(directory, ignore_errors=True)
            return await self.download(quality, number)
        except KeyError:
            shutil.rmtree(directory, ignore_errors=True)
            return None
        else:
            if os.stat(path).st_size < file_size:
                shutil.rmtree(directory, ignore_errors=True)
                return None

            return path
