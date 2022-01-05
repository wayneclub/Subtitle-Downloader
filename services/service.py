#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""
import locale
import logging
import os
import requests


class Service(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url.strip()

        if args.output:
            self.output = args.output.strip()
        else:
            self.output = os.getcwd()

        if args.season:
            self.download_season = int(args.season)
        else:
            self.download_season = None

        self.last_episode = args.last_episode

        self.locale = args.locale

        if args.region:
            self.region = args.region.upper()
        else:
            self.region = None

        self.session = requests.Session()

        self.default_language = self.get_default_language(self.locale)

    def get_default_language(self, lang=""):
        current_locale = locale.getdefaultlocale()[0]

        if 'zh' in current_locale or (lang and 'zh' in lang):
            return 'zh-Hant'
        else:
            return 'en'
