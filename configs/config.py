#!/usr/bin/python3
# coding: utf-8

"""
This module is for default setting.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import pytomlpp

app_name = "Subtitle-Downloader"
__version__ = "2.0.0"


class Config:
    """
    Config module
    """

    def __init__(self, **kwargs: Any):
        self.locale: str = kwargs.get('locale') or ''
        self.subtitles: dict = kwargs.get('subtitles') or {}
        self.credentials: dict = kwargs.get('credentials') or {}
        self.directories: dict = kwargs.get('directories') or {}
        self.headers: dict = kwargs.get('headers') or {}
        self.nordvpn: dict = kwargs.get('nordvpn') or {}
        self.proxies: dict = kwargs.get('proxies') or {}

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        """Load toml"""
        if not path.exists():
            raise FileNotFoundError(f"Config file path ({path}) was not found")
        if not path.is_file():
            raise FileNotFoundError(
                f"Config file path ({path}) is not to a file.")
        return cls(**pytomlpp.load(path))


class Directories:
    """
    Directories module
    """

    def __init__(self) -> None:
        self.package_root = Path(__file__).resolve().parent.parent
        self.configuration = self.package_root / 'configs'
        self.downloads = self.package_root / 'downloads'
        self.cookies = self.package_root / 'cookies'
        self.logs = self.package_root / 'logs'


class Filenames:
    """
    Filenames module
    """

    def __init__(self) -> None:
        self.log = directories.logs / "{app_name}_{log_time}.log"
        self.config = directories.configuration / "{service}.toml"
        self.root_config: Path = directories.package_root / "user_config.toml"


directories = Directories()
filenames = Filenames()

config = Config.from_toml(filenames.root_config)
if not config.directories.get('cookies'):
    config.directories['cookies'] = directories.cookies
if not config.directories.get('downloads'):
    config.directories['downloads'] = directories.downloads
config.directories['logs'] = directories.logs
credentials = config.credentials
user_agent = config.headers['User-Agent']
