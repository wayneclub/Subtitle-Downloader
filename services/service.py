#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""
from __future__ import annotations
import html
import os
import ssl
import sys
from http.cookiejar import MozillaCookieJar
from urllib3 import poolmanager
from typing import Optional, Union
from pathlib import Path
import requests
import opencc
from requests import adapters
from tmdbv3api import TMDb, TV, Movie
from natsort import natsorted
from configs.config import config, credentials, filenames, user_agent
from utils.ripprocess import ripprocess


class Service(object):
    """
    BaseService
    """

    def __init__(self, args):
        self.logger = args.log
        self.url = args.url.strip()
        self.platform = args.platform
        self.cookies = {}
        self.config = self.validate_config(args.config)
        self.movie = False

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

        self.session = requests.Session()
        self.session.mount('https://', TLSAdapter())
        self.session.headers = {
            'user-agent': user_agent
        }
        self.session.cookies.update(self.cookies)
        self.cookies = self.session.cookies.get_dict()

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

        self.download_path = config.directories['downloads']

        self.subtitle_language = self.get_language_list(args)

        self.tmdb = TMDb()
        self.tmdb.api_key = credentials['TMDB']['api_key']

    def validate_config(self, service_config):
        """ validate service config """

        if service_config.get('credentials') == 'cookies':
            if credentials[self.platform].get('cookies'):
                self.cookies = self.get_cookie_jar(
                    service_config.get('required'))
            else:
                self.logger.error(
                    '\nMissing define %s\'s cookies in %s', self.platform, filenames.root_config)
                sys.exit(1)
        elif service_config.get('credentials') == 'email':
            if not credentials[self.platform].get('email') and not credentials[self.platform].get('password'):
                self.logger.error(
                    '\nMissing define %s\'s email and password in %s', self.platform, filenames.root_config)
                sys.exit(1)

        return service_config

    def get_cookie_jar(self, required) -> Optional[MozillaCookieJar]:
        """Get Profile's Cookies as Mozilla Cookie Jar if available."""

        cookie_file = Path(
            config.directories['cookies']) / credentials[self.platform]['cookies']
        if cookie_file.is_file():
            cookie_jar = MozillaCookieJar(cookie_file)
            cookie_file.write_text(html.unescape(
                cookie_file.read_text("utf8")), "utf8")
            cookie_jar.load(ignore_discard=True, ignore_expires=True)

            if required and required not in str(cookie_jar):
                self.logger.warning(
                    "\nMissing \"%s\" in %s.\nPlease login to streaming services and renew cookies...",
                    required,
                    os.path.basename(cookie_file))
                os.remove(cookie_file)
                sys.exit(1)

            return cookie_jar
        else:
            self.logger.error(
                f"\nPlease put {os.path.basename(cookie_file)} in {Path(config.directories['cookies'])}")
            sys.exit(1)

    def get_language_list(self, args):
        """ Get language list """

        subtitle_language = args.subtitle_language
        if not subtitle_language:
            subtitle_language = config.default_language

        return tuple([
            language for language in subtitle_language.split(',')])

    def get_movie_info(self, title, title_aliases):
        """ Get movie details from TMDB """

        if not title_aliases:
            title_aliases = []

        title_aliases.append(opencc.OpenCC('t2s.json').convert(title))
        movie = Movie()

        results = movie.search(title.strip())

        if results:
            return results[0]
        else:
            for alias in title_aliases:
                results = movie.search(alias.strip())
                if results:
                    return results[0]

    def get_series_info(self, title, title_aliases):
        """Get series details from TMDB """

        if not title_aliases:
            title_aliases = []

        title_aliases.append(opencc.OpenCC('t2s.json').convert(title))

        tv = TV()
        results = tv.search(title.strip())

        if results:
            return results[0]
        else:
            for alias in title_aliases:
                results = tv.search(alias.strip())
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


# class TLSAdapter(adapters.HTTPAdapter):

#     def init_poolmanager(self, connections, maxsize, block=False):
#         """Create and initialize the urllib3 PoolManager."""
#         ctx = ssl.create_default_context()
#         ctx.set_ciphers('DEFAULT@SECLEVEL=1')
#         self.poolmanager = poolmanager.PoolManager(
#             num_pools=connections,
#             maxsize=maxsize,
#             block=block,
#             ssl_version=ssl.PROTOCOL_TLS,
#             ssl_context=ctx)


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
