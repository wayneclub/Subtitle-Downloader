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
from selenium import webdriver
import chromedriver_autoinstaller
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
            else:
                logger.error(
                    "Failure - API is accessible but sth is not right. Response codde : %s", response.status_code)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as error:
            logger.error(
                "Failure - Unable to establish connection: %s.", error)
        except Exception as error:
            logger.error("Failure - Unknown error occurred: %s.", error)

    return False


def driver_init(headless=True):
    """Initial selenium"""

    kill_process()
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('window-size=1280,800')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument("--mute-audio")
    options.add_argument('--autoplay-policy=no-user-gesture-required')
    options.add_argument('--lang=zh-TW')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    prefs = {'intl.accept_languages': 'zh,zh_TW',
             'credentials_enable_service': False, 'profile.password_manager_enabled': False,
             'profile.default_content_setting_values': {'images': 2, 'plugins': 2, 'popups': 2, 'geolocation': 2, 'notifications': 2}}
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option(
        'excludeSwitches', ['enable-automation'])
    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome('chromedriver', options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                           "userAgent": user_agent})
    # driver.set_page_load_timeout(3000)
    return driver


def get_network_url(driver, search_url, lang=""):
    """Get url from network"""

    _ = get_locale(__name__, lang)
    url = ''
    delay = 0
    logs = tuple()
    while not url:
        logs += tuple(driver.execute_script(
            "return window.performance.getEntries();"))

        url = next((log['name'] for log in logs
                    if re.search(search_url, log['name'])), None)
        delay += 1

        if delay > 60:
            logger.error(_("\nTimeout, please retry."))
            sys.exit(1)
    return url


def kill_process():
    """Kill process"""

    os.system('killall chromedriver > /dev/null 2>&1')


if __name__:
    logger = logging.getLogger(__name__)
