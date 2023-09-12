#!/usr/bin/python3
# coding: utf-8

"""
This module is for common tool.
"""
import os
import locale
import logging
import gettext
import re
import sys
from natsort import natsorted
import requests
import validators
from configs.config import user_agent
from constants import ISO_6391


class EpisodesNumbersHandler(object):
    """
    Convert user-input episode range to list of int numbers
    """

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
                raise ValueError(f"wrong number: {number}")
            return self.number_range(int(start), int(end))

        if "~" in number:
            start, _ = number.split("~")
            if start.strip() == "":
                raise ValueError(f"wrong number: {number}")
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


def get_locale(name, lang=""):
    """Get environment locale"""

    if locale.getdefaultlocale():
        current_locale = locale.getdefaultlocale()[0]
    else:
        current_locale = 'en'

    if lang and 'zh' in lang:
        current_locale = 'zh'

    if 'zh' in current_locale:
        locale_ = gettext.translation(
            name, localedir='locales', languages=['zh-Hant'])
        locale_.install()
        return locale_.gettext
    else:
        return gettext.gettext


def get_language_code(lang=''):
    """Convert subtitle language code to ISO_6391 format"""

    uniform = lang.lower().replace('_', '-')
    if ISO_6391.get(uniform):
        return ISO_6391.get(uniform)
    else:
        return lang


def get_all_languages(available_languages, subtitle_language, locale_):
    """Get all subtitles language"""

    _ = get_locale(__name__, locale_)

    if available_languages:
        available_languages = sorted(available_languages)

    if 'all' in subtitle_language:
        subtitle_language = available_languages

    intersect = set(subtitle_language).intersection(
        set(available_languages))

    if not intersect:
        logger.error(
            _("\nUnsupport %s subtitle, available languages: %s"), ", ".join(subtitle_language), ", ".join(available_languages))
        return False

    if len(intersect) != len(subtitle_language):
        logger.error(
            _("\nUnsupport %s subtitle, available languages: %s"), ", ".join(set(subtitle_language).symmetric_difference(intersect)), ", ".join(available_languages))
        return False


def check_url_exist(url, headers=None):
    """Validate url exist"""

    if validators.url(url):

        if not headers:
            headers = {'user-agent': user_agent}
        try:
            response = requests.head(
                url, headers=headers, timeout=10)
            if response.ok:
                return True

        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as error:
            logger.error(
                "Failure - Unable to establish connection: %s.", error)
        except Exception as error:
            logger.error("Failure - Unknown error occurred: %s.", error)

    return False


if __name__:
    logger = logging.getLogger(__name__)
