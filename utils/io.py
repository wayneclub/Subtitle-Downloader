from __future__ import annotations
from typing import Optional, Union
from pathlib import Path
import html
import os
import sys
from http.cookiejar import MozillaCookieJar
import rtoml

from configs.config import config, credentials


def load_toml(path: Union[Path, str]) -> dict:
    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_file():
        return {}
    return rtoml.load(path)
