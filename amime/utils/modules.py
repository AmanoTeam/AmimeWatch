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

import glob
import importlib
from types import ModuleType
from typing import List

from amime import log

modules: List[ModuleType] = []


def load(bot):
    files = glob.glob(f"amime/modules/**/*.py", recursive=True)
    files = sorted(files, key=lambda file: file.split("/")[2])

    for file_name in files:
        try:
            module = importlib.import_module(
                file_name.replace("/", ".").replace(".py", "")
            )
            modules.append(module)
        except BaseException:
            log.error(f"Failed to import the module: {file_name}", exc_info=True)
            continue

        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.add_handler(*handler)

    log.info(
        f"{len(modules)} module{'s' if len(modules) != 1 else ''} imported successfully!"
    )


def reload(bot):
    for index, module in enumerate(modules):
        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.remove_handler(*handler)

        module = importlib.reload(module)
        modules[index] = module

        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.add_handler(*handler)

    log.info(
        f"{len(modules)} module{'s' if len(modules) != 1 else ''} reloaded successfully!"
    )
