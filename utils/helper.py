#!/usr/bin/python3
# coding: utf-8

"""
This module is for common tool.
"""
import os
import locale
import logging
import gettext
from pathlib import Path
import re
from operator import itemgetter
import multiprocessing
from urllib import request
from urllib.error import HTTPError, URLError
import orjson
from tqdm import tqdm
from selenium import webdriver
import chromedriver_autoinstaller

from configs.config import Config


def get_locale(name, lang=""):
    current_locale = locale.getdefaultlocale()[0]
    if lang and 'zh' in lang:
        current_locale = 'zh'

    if 'zh' in current_locale:
        locale_ = gettext.translation(
            name, localedir='locales', languages=['zh-Hant'])
        locale_.install()
        return locale_.gettext
    else:
        return gettext.gettext


def check_url_exist(url, print_error=False):
    """Check url exist"""
    try:
        request.urlopen(url)
    except HTTPError as exception:
        # Return code error (e.g. 404, 501, ...)
        if print_error:
            logger.error("HTTPError: %s", exception.code)
        return False
    except URLError as exception:
        # Not an HTTP-specific error (e.g. connection refused)
        if print_error:
            logger.error("URLError: %s", exception.reason)
        return False
    else:
        return True


def driver_init(headless=True):
    """Get html render by js"""
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
                           "userAgent": Config().get_user_agent()})
    # driver.set_page_load_timeout(3000)
    return driver


def get_network_url(driver, search_url, lang=""):
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
    os.system('killall chromedriver > /dev/null 2>&1')


def pretty_print_json(json_obj):
    return orjson.dumps(
        json_obj, option=orjson.OPT_INDENT_2).decode('utf-8')


def fix_filename(name, max_length=255):
    return re.sub(r'[/\\:|<>"?*\0-\x1f]|^(AUX|COM[1-9]|CON|LPT[1-9]|NUL|PRN)(?![^.])|^\s|[\s.]$', "", name[:max_length], flags=re.IGNORECASE)


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url, output_path, lang=""):
    _ = get_locale(__name__, lang)
    if check_url_exist(url):
        with DownloadProgressBar(unit='B', unit_scale=True,
                                 miniters=1, desc=os.path.basename(output_path)) as t:
            request.urlretrieve(
                url, filename=output_path, reporthook=t.update_to)
    else:
        logger.warning(_("\nFile not found!"))


def download_files(files):
    cpus = multiprocessing.cpu_count()
    max_pool_size = 8
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)

    lang_paths = []
    for file in sorted(files, key=itemgetter('name')):
        if 'url' in file and 'name' in file and 'path' in file:
            if 'segment' in file and file['segment']:
                extension = Path(file['name']).suffix
                sequence = str(lang_paths.count(file['path'])).zfill(3)
                file_name = os.path.join(file['path'], file['name'].replace(
                    extension, f'-seg_{sequence}{extension}'))
                lang_paths.append(file['path'])
            else:
                file_name = os.path.join(file['path'], file['name'])
            pool.apply_async(download_file, args=(
                file['url'], file_name))
    pool.close()
    pool.join()


def download_audio(m3u8_url, output):
    os.system(
        f'ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "{m3u8_url}" -c copy "{output}" -preset ultrafast -loglevel warning -hide_banner -stats')


if __name__:
    logger = logging.getLogger(__name__)
