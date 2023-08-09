#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""
import locale
import logging
import os
import ssl
from natsort import natsorted
import requests
from configs.config import Config
from utils.ripprocess import ripprocess


class Service(object):

    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url.strip()

        if args.output:
            self.output = args.output.strip()
        else:
            self.output = None

        if args.season:
            self.download_season = EpisodesNumbersHandler(
                args.season).get_episodes()
        else:
            self.download_season = []

        if args.episode:
            self.download_episode = EpisodesNumbersHandler(
                args.episode).get_episodes()
        else:
            self.download_episode = []

        self.last_episode = args.last_episode

        self.locale = args.locale

        self.config = Config()
        self.session = requests.Session()
        self.session.mount('https://', TLSAdapter())
        self.user_agent = self.config.get_user_agent()
        self.session.headers = {
            'user-agent': self.user_agent
        }

        self.ip_info = args.proxy
        self.proxy = self.ip_info['proxy']
        if self.proxy:
            self.session.proxies.update(self.proxy)
            self.proxy = list(self.proxy.values())[0]
        else:
            self.proxy = ''

        if args.region:
            self.region = args.region.upper()
        else:
            self.region = self.ip_info['country']

        self.ripprocess = ripprocess()

        self.download_path = self.config.paths()['downloads']

        self.default_language = self.get_default_language(self.locale)

    def get_default_language(self, lang=""):
        current_locale = locale.getdefaultlocale()[0]

        if 'zh' in current_locale or (lang and 'zh' in lang):
            return 'zh-Hant'
        else:
            return 'en'

class TLSAdapter(requests.adapters.HTTPAdapter):

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

class EpisodesNumbersHandler(object):
    def __init__(self, episodes):
        self.episodes = episodes

    def number_range(self, start: int, end: int):
        if list(range(start, end + 1)) != []:
            return list(range(start, end + 1))

        if list(range(end, start + 1)) != []:
            return list(range(end, start + 1))

        return [start]

    def list_number(self, number: str):
        if number.isdigit():
            return [int(number)]

        if number.strip() == "~" or number.strip() == "":
            return self.number_range(1, 999)

        if "-" in number:
            start, end = number.split("-")
            if start.strip() == "" or end.strip() == "":
                raise ValueError("wrong number: {}".format(number))
            return self.number_range(int(start), int(end))

        if "~" in number:
            start, _ = number.split("~")
            if start.strip() == "":
                raise ValueError("wrong number: {}".format(number))
            return self.number_range(int(start), 999)

        return

    def sort_numbers(self, numbers):
        sorted_numbers = []
        for number in numbers.split(","):
            sorted_numbers += self.list_number(number.strip())

        return natsorted(list(set(sorted_numbers)))

    def get_episodes(self):
        return (
            self.sort_numbers(
                str(self.episodes).lstrip("0")
            )
            if self.episodes
            else self.sort_numbers("~")
        )
