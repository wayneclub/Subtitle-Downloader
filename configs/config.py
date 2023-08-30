#!/usr/bin/python3
# coding: utf-8

"""
This module is for config.
"""
from __future__ import annotations
from os.path import dirname
from pathlib import Path
from typing import Any
import rtoml

app_name = "Subtitle-Downloader"
__version__ = "1.0.0"


dir_path = dirname(dirname(__file__)).replace("\\", "/")

default_path = {
    "cookies":  f"{dir_path}/cookies",
    "downloads": f"{dir_path}/downloads",
    "logs": f"{dir_path}/logs",
}


class Platform:
    """
    Define all streaming service name
    """

    KKTV = "KKTV"
    LINETV = "LineTV"
    FRIDAYVIDEO = "FridayVideo"
    CATCHPLAY = 'CatchPlay'
    IQIYI = "iQIYI"
    WETV = 'WeTV'
    VIU = "Viu"
    NOWE = 'NowE'
    NOWPLAYER = 'NowPlayer'
    DISNEYPLUS = "DisneyPlus"
    HBOGOASIA = "HBOGOAsia"
    APPLETVPLUS = 'AppleTVPlus'
    ITUNES = "iTunes"


VPN = {
    "proxies": "http://127.0.0.1:7890",
    "nordvpn": {
        "port": "80",
        # Advanced configuration (https://my.nordaccount.com/dashboard/nordvpn/)
        "username": "",
        "password": "",
        "http": "http://{email}:{passwd}@{ip}:{port}",
    },
    "private": {
        "port": "8080",
        # Enter the email address of your VPN account here
        "email": "enter your email address here",
        # Enter the password of your VPN account here
                "passwd": "enter your password here",
                "http": "http://{email}:{passwd}@{ip}:{port}",
    },
}


class Config:
    def __init__(self, **kwargs: Any):
        self.default_language: str = kwargs.get("default-language") or ""
        self.credentials: dict = kwargs.get("credentials") or {}
        self.directories: dict = kwargs.get("directories") or {}
        self.headers: dict = kwargs.get("headers") or {}
        self.nordvpn: dict = kwargs.get("nordvpn") or {}

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        if not path.exists():
            raise FileNotFoundError(f"Config file path ({path}) was not found")
        if not path.is_file():
            raise FileNotFoundError(
                f"Config file path ({path}) is not to a file.")
        return cls(**rtoml.load(path))

    def vpn(self):
        return VPN


class Directories:
    def __init__(self) -> None:
        self.package_root = Path(__file__).resolve().parent.parent
        self.configuration = self.package_root / 'configs'
        self.downloads = self.package_root / 'downloads'
        self.cookies = self.package_root / 'cookies'
        self.logs = self.package_root / 'logs'


class Filenames:
    def __init__(self) -> None:
        self.log = directories.logs / "{app_name}_{log_time}.log"
        self.config = directories.configuration / "{service}.toml"
        self.root_config: Path = directories.package_root / "user_config.toml"


def mergeDictsOverwriteEmpty(d1, d2):
    res = d2.copy()
    for k, v in d1.items():
        if k not in d2 or d2[k] == '':
            res[k] = v
    return res


directories = Directories()
filenames = Filenames()

config = Config.from_toml(filenames.root_config)
config.directories = mergeDictsOverwriteEmpty(default_path, config.directories)
credentials = config.credentials
user_agent = config.headers['User-Agent']
