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
import platform
import re
from operator import itemgetter
import multiprocessing
from urllib import request
from urllib.error import HTTPError, URLError
import requests
from requests.adapters import HTTPAdapter
import orjson
from tqdm import tqdm
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from urllib3.util import Retry
# from common.subtitle import


class HTTPMethod:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Platform:
    NETFLIX = "Netflix"
    KKTV = "KKTV"
    LINETV = "LineTV"
    FRIDAY = "friDay"
    IQIYI = "iQIYI"
    DISNEY = "Disney+"
    HBOGO = "HBOGO"
    VIU = "Viu"


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


def http_request(session=requests.Session(), url="", method="", headers="", kwargs="", raw=False):

    if headers:
        session.headers = headers
    else:
        # session.headers = {
        #     'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        # }
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }

    session.timeout = 10
    adapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2))
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    if method == HTTPMethod.GET:
        req = session.get(url)
    elif method == HTTPMethod.POST:
        req = session.post(url, **kwargs)
    elif method == HTTPMethod.PUT:
        req = session.put(url, **kwargs)
    elif method == HTTPMethod.DELETE:
        req = session.delete(url, **kwargs)
    else:
        exit(1)

    if req.ok:
        if raw:
            return req.text
        else:
            return req.json()
    else:
        logger.error("\n%s", req.text)
        exit(1)


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
    if platform.system() == 'Windows':
        driver = webdriver.Chrome(ChromeDriverManager(
            log_level=0).install(), options=options)
    else:
        driver = webdriver.Chrome('chromedriver', options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
    # driver.get('chrome://settings/clearBrowserData')
    driver.set_page_load_timeout(120)
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
            exit(1)
    return url


def kill_process():
    os.system('killall chromedriver > /dev/null 2>&1')


def get_ip_location():
    return http_request(url='https://ipinfo.io/json', method=HTTPMethod.GET)


def save_html(html_source, file='test.html'):
    with open(file, 'w') as writter:
        writter.write(str(html_source))


def pretty_print_json(json_obj):
    return orjson.dumps(
        json_obj, option=orjson.OPT_INDENT_2).decode('utf-8')


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


def download_file_multithread(urls, file_names, output_path=""):
    cpus = multiprocessing.cpu_count()
    max_pool_size = 8
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)
    for url, file_name in zip(urls, file_names):
        pool.apply_async(download_file, args=(
            url, os.path.join(output_path, file_name)))
    pool.close()
    pool.join()


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
                sequence = str(lang_paths.count(file['path'])).zfill(2)
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
