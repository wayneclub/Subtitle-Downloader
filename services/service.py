#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""
import locale
import logging
import sys
import requests
import ssl
import opencc
from tmdbv3api import TMDb, Search
from natsort import natsorted
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

        # self.default_language = self.get_default_language(self.locale)
        self.subtitle_language = self.get_language_list(args)

        self.tmdb = TMDb()
        self.tmdb.api_key = self.config.credential("TMDB")['api_key']
        self.search = Search()

    def get_language_code(self, lang):
        language_code = self.config.get_language_code(lang)
        if language_code:
            return language_code
        else:
            self.logger.error("\nMissing codec mapping: %s", lang)
            sys.exit(1)

    def get_language_list(self, args):
        subtitle_language = args.subtitle_language
        if not subtitle_language:
            subtitle_language = self.config.get_default_language()

        return tuple([
            language for language in subtitle_language.split(',')])

    def get_movie_info(self, title, release_year="", title_aliases=[]):
        title_aliases.append(opencc.OpenCC('t2s.json').convert(title))

        query = {'query': title.strip()}
        if release_year:
            query['year'] = int(release_year)

        results = self.search.movies(query)

        if results:
            return results[0]
        else:
            for alias in title_aliases:
                query['query'] = alias.strip()
                results = self.search.movies(query)
                if results:
                    return results[0]

    def get_series_info(self, title, title_aliases=[]):
        title_aliases.append(opencc.OpenCC('t2s.json').convert(title))

        query = {'query': title.strip()}

        results = self.search.tv_shows(query)

        if results:
            return results[0]
        else:
            for alias in title_aliases:
                query['query'] = alias.strip()
                results = self.search.tv_shows(query)
                if results:
                    return results[0]

    def replace_title(self, title):
        return title.replace(":", " ").replace("!", " ").replace("?", " ").replace("#", " ").replace("’", "'").replace("  ", " ").strip()


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
