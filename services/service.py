#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""
from __future__ import annotations
from utils.ripprocess import ripprocess
from utils.proxy import get_ip_info, get_proxy
from utils.helper import EpisodesNumbersHandler
from configs.config import config, credentials, filenames, user_agent
from tmdbv3api import TMDb, TV, Movie
import opencc
import html
import os
import ssl
import sys
from http.cookiejar import MozillaCookieJar
from typing import Optional
from pathlib import Path
import requests
import urllib3
urllib3.disable_warnings()


class Service(object):
    """
    BaseService
    """

    # list of ip regions required to use the service. empty list == global available.
    GEOFENCE: list[str] = []

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

        self.ip_info = get_ip_info()
        self.logger.info(
            'ip: %s (%s)', self.ip_info['ip'], self.ip_info['country'])

        proxy = args.proxy or next(iter(self.GEOFENCE), None)
        if proxy:
            if len("".join(i for i in proxy if not i.isdigit())) == 2:  # e.g. ie, ie12, us1356
                proxy = get_proxy(region=proxy, ip_info=self.ip_info)
            if proxy:
                if "://" not in proxy:
                    # assume a https proxy port
                    proxy = f"https://{proxy}"
                self.session.proxies.update({"all": proxy})
                self.logger.info(" + Set Proxy")
            else:
                self.logger.info(
                    " + Proxy was skipped as current region matches")

        if args.region:
            self.region = args.region.upper()
        else:
            self.region = self.ip_info['country']

        self.ripprocess = ripprocess()

        self.download_path = config.directories['downloads']

        self.subtitle_language = self.get_language_list(args)

        tmdb = TMDb()
        tmdb.api_key = credentials['TMDB']['api_key']

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


class TLSAdapter(requests.adapters.HTTPAdapter):

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)
