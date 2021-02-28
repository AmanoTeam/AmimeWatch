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

import os

from tortoise import fields, Tortoise
from tortoise.models import Model


class Chats(Model):
    id = fields.IntField(pk=True)
    title = fields.TextField()
    username = fields.CharField(max_length=32)
    language = fields.CharField(max_length=6)


class Collaborators(Model):
    id = fields.IntField(pk=True)
    user = fields.IntField()
    language = fields.CharField(max_length=6)


class Episodes(Model):
    id = fields.IntField(pk=True)
    anime = fields.IntField()
    file_id = fields.TextField()
    number = fields.IntField()
    duration = fields.IntField()
    language = fields.CharField(max_length=6)


class Favorites(Model):
    id = fields.IntField(pk=True)
    user = fields.IntField()
    item = fields.IntField()
    type = fields.CharField(max_length=7)


class Users(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    username = fields.CharField(max_length=32)
    language_bot = fields.CharField(max_length=6)
    language_anime = fields.CharField(max_length=6)
    is_collaborator = fields.BooleanField()


class Viewed(Model):
    id = fields.IntField(pk=True)
    user = fields.IntField()
    item = fields.IntField()
    type = fields.CharField(max_length=7)


class Watched(Model):
    id = fields.IntField(pk=True)
    user = fields.IntField()
    episode = fields.IntField()


async def connect_database():
    await Tortoise.init(
        {
            "connections": {
                "bot_db": os.getenv(
                    "DATABASE_URL", "sqlite://amime/database/database.sqlite"
                )
            },
            "apps": {"bot": {"models": [__name__], "default_connection": "bot_db"}},
        }
    )

    # Generate the schema
    await Tortoise.generate_schemas()
