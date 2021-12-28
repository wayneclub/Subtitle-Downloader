#!/usr/bin/python3
# coding: utf-8

"""
This module is for common tool.
"""
import os
from pathlib import Path
import platform
import re
import time
import multiprocessing
from urllib import request
from urllib.error import HTTPError, URLError
import requests
from requests.adapters import HTTPAdapter
import orjson
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from urllib3.util import Retry
from pygments import highlight, lexers, formatters
import subtitle_tool


class HTTPMethod:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url, output_path):
    if check_url_exist(url):
        with DownloadProgressBar(unit='B', unit_scale=True,
                                 miniters=1, desc=os.path.basename(output_path)) as t:
            request.urlretrieve(
                url, filename=output_path, reporthook=t.update_to)
    else:
        print("找不到檔案")


def download_file_multithread(urls, output_path):

    cpus = multiprocessing.cpu_count()
    max_pool_size = 8
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)
    for url in urls:
        pool.apply_async(download_file, args=(
            url, os.path.join(output_path, os.path.basename(url))))
    pool.close()
    pool.join()


def download_audio(m3u8_url, output):
    os.system(
        f'ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "{m3u8_url}" -c copy "{output}" -preset ultrafast -loglevel warning -hide_banner -stats')


def http_request(session=requests.Session(), url="", method="", headers="", kwargs="", raw=False):

    if headers:
        session.headers = headers
    else:
        session.headers = {
            'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }

    session.timeout = 10
    adapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=5))
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
        print(f'\n{pretty_print_json(orjson.loads(req.text))}')
        exit(1)


def check_url_exist(url, print_error=False):
    """Check url exist"""
    try:
        request.urlopen(url)
    except HTTPError as exception:
        # Return code error (e.g. 404, 501, ...)
        if print_error:
            print(f"HTTPError: {exception.code}")
        return False
    except URLError as exception:
        # Not an HTTP-specific error (e.g. connection refused)
        if print_error:
            print(f"URLError: {exception.reason}")
        return False
    else:
        return True


def get_static_html(url, json_request=False):
    """Get static html"""
    try:
        headers = {
            'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }
        req = request.Request(url, headers=headers)
        response = request.urlopen(req)

        if json_request:
            try:
                return orjson.loads(response.read())
            except orjson.decoder.JSONDecodeError:
                print("String could not be converted to JSON")
        else:
            return BeautifulSoup(response.read(), 'lxml')

    except HTTPError as exception:
        print(f"HTTPError: {exception.code}")
    except URLError as exception:
        print(f"URLError: {(exception.reason)}")


def get_dynamic_html(url, headless=True):
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
    prefs = {'intl.accept_languages': 'zh,zh_TW',
             'credentials_enable_service': False, 'profile.password_manager_enabled': False}
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    if platform.system() == 'Windows':
        driver = webdriver.Chrome(ChromeDriverManager(
            log_level=0).install(), options=options)
    else:
        driver = webdriver.Chrome('chromedriver', options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
    # driver.get('chrome://settings/clearBrowserData')
    driver.get(url)
    driver.set_page_load_timeout(110)
    return driver


def get_network_url(driver, search_url):
    url = ''
    delay = 0
    logs = []
    while not url:
        time.sleep(2)
        logs += driver.execute_script(
            "return window.performance.getEntries();")

        url = next((log['name'] for log in logs
                    if re.search(search_url, log['name'])), None)
        delay += 1

        if delay > 60:
            print("找不到data，請重新執行")
            exit(1)
    return url


def find_visible_element_by_id(driver, id_text):
    return WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, id_text)))


def find_visible_element_by_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, xpath)))


def find_visible_elements_by_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, xpath)))


def find_visible_element_clickable_by_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath)))


def find_present_element_by_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath)))


def get_locale(driver):
    return driver.execute_script("return window.navigator.language")


def convert_subtitle(folder_path, ott=''):
    if os.path.exists(folder_path):
        for index, file in enumerate(sorted(os.listdir(folder_path))):
            extenison = Path(file).suffix
            if extenison != '.srt':
                if index == 0:
                    print(
                        f"\n將{extenison}轉換成.srt：\n---------------------------------------------------------------")
                subtitle = os.path.join(folder_path, file)
                subtitle_tool.convert_subtitle(subtitle, '', True, False)
        if ott:
            subtitle_tool.archive_subtitle(os.path.normpath(folder_path), ott)


def merge_subtitle(folder_path, file_name):
    if os.path.exists(folder_path):
        os.system(f'python subtitle_tool.py "{folder_path}" -m "{file_name}"')


def kill_process():
    os.system('killall chromedriver > /dev/null 2>&1')


def get_ip_location():
    return http_request(url='https://ipinfo.io/json', method=HTTPMethod.GET)


def save_html(html_source, file='test.html'):
    with open(file, 'w') as writter:
        writter.write(str(html_source))


def pretty_print_json(json_obj):
    formatted_json = orjson.dumps(
        json_obj, option=orjson.OPT_INDENT_2).decode('utf-8')
    return highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
