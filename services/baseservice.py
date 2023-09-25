#!/usr/bin/python3
# coding: utf-8

"""
This module is base service
"""
from __future__ import annotations
import html
import os
import ssl
import sys
from http.cookiejar import MozillaCookieJar
from typing import Optional
from pathlib import Path
import requests
from opencc import OpenCC
from pwinput import pwinput

from configs.config import config, credentials, filenames, user_agent
from constants import SUBTITLE_FORMAT
from utils.ripprocess import RipProcess
from utils.proxy import get_ip_info, get_proxy
from utils.helper import EpisodesNumbersHandler
from utils.io import get_tmdb_info


class BaseService(object):
    """
    BaseService
    """

    # list of ip regions required to use the service. empty list == global available.
    GEOFENCE: list[str] = []

    def __init__(self, args):
        self.logger = args.log
        self.url = args.url.strip()
        self.service = args.service
        self.platform = self.service['name']
        self.locale = args.locale

        self.cookies = {}
        self.session = requests.Session()
        self.session.mount('https://', TLSAdapter())
        self.session.headers = {
            'user-agent': user_agent
        }
        self.config = self.validate_config(args.config)
        self.movie = False

        if args.output and os.path.exists(args.output):
            config.directories['downloads'] = args.output.strip()

        self.download_path = config.directories['downloads']

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

        self.session.cookies.update(self.cookies)
        self.cookies = self.session.cookies.get_dict()

        proxy = args.proxy or next(iter(self.GEOFENCE), None)
        if proxy:
            self.set_proxy(proxy)

        self.ripprocess = RipProcess()

        self.subtitle_language = self.get_language_list(args.subtitle_language)
        self.subtitle_format = self.get_subtitle_format(args.subtitle_format)

    def validate_config(self, service_config):
        """ Validate service config """

        if service_config and 'cookies' in service_config.get('credentials'):
            if credentials[self.platform].get('cookies'):
                self.cookies = self.get_cookie_jar(
                    service_config.get('required'))
            else:
                self.logger.error('\n%s\'s cookies isn\'t set in %s',
                                  self.platform, filenames.root_config)
                sys.exit(1)

        if service_config and 'email' in service_config.get('credentials'):
            if not credentials[self.platform].get('email') and not credentials[self.platform].get('password'):
                credentials[self.platform]['email'] = input("Email: ").strip()
                credentials[self.platform]['password'] = pwinput().strip()

        return service_config

    def get_cookie_jar(self, required) -> Optional[MozillaCookieJar]:
        """ Get profile's cookies as Mozilla Cookie Jar if available. """

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

    def set_proxy(self, proxy):
        """Set proxy: support dynamic proxy in each service"""

        if len("".join(i for i in proxy if not i.isdigit())) == 2:  # e.g. ie, ie12, us1356
            proxy = get_proxy(
                region=proxy, geofence=self.GEOFENCE, platform=self.platform)

        if proxy:
            if "://" not in proxy:
                # assume a https proxy port
                proxy = f"https://{proxy}"
            self.session.proxies.update({"all": proxy})
            self.logger.info(" + Set Proxy")
        else:
            self.logger.info(" + Proxy was skipped as current region matches")

    def get_language_list(self, subtitle_language):
        """ Get language list """

        if not subtitle_language:
            subtitle_language = config.subtitles['default-language']

        return tuple([
            language for language in subtitle_language.split(',')])

    def get_subtitle_format(self, subtitle_format):
        """ Get subtitle default format """

        if not subtitle_format or not subtitle_format in SUBTITLE_FORMAT:
            subtitle_format = config.subtitles['default-format']
        return subtitle_format

    def get_title_info(self, title="", release_year="", title_aliases=None, is_movie=False):
        """
        Get title info from TMDB
        """
        title_info = {}
        if not title_aliases:
            title_aliases = []

        title_aliases.append(OpenCC('t2s.json').convert(title))

        results = get_tmdb_info(
            title=title, release_year=release_year, is_movie=is_movie)

        if results.get('results'):
            title_info = results.get('results')[0]
        else:
            for alias in title_aliases:
                results = get_tmdb_info(title=alias.strip(),
                                        release_year=release_year, is_movie=is_movie)
                if results.get('results'):
                    title_info = results.get('results')[0]
                    break

        if title_info:
            if title_info.get('name'):
                title_info['title'] = title_info['name']
            if title_info.get('release_date'):
                title_info['release_year'] = title_info['release_date'][:4]
            if title_info.get('first_air_date'):
                title_info['release_year'] = title_info['first_air_date'][:4]

        self.logger.debug('tmdb: ', title_info)
        return title_info


class TLSAdapter(requests.adapters.HTTPAdapter):
    """
    Fix openssl issue
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)
