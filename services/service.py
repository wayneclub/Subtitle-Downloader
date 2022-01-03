#!/usr/bin/python3
# coding: utf-8

"""
This module is default service
"""

import logging
import os
import requests


class Service(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.locale = args.locale
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

        self.session = requests.Session()
