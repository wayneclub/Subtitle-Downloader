#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from HBOGO Asia
"""
import sys
import re
import os
import shutil
import platform
import logging
import uuid
import json
from os.path import dirname
from getpass import getpass
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from urllib.parse import urlparse
import requests
from common.utils import get_locale, Platform, http_request, HTTPMethod, pretty_print_json, download_files
from common.subtitle import convert_subtitle
from services.service import Service


class Netflix(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        # self._ = get_locale(__name__, self.locale)
        self.username = args.email
        self.password = args.password

        dirPath = dirname(dirname(__file__)).replace("\\", "/")

        self.config = {
            "cookies_file": f"{dirPath}/cookies_nf.txt",
            "cookies_txt": f"{dirPath}/cookies.txt",
            "metada_language": "zh-Hant"
        }

    def get_build(self, cookies):
        BUILD_REGEX = r'"BUILD_IDENTIFIER":"([a-z0-9]+)"'

        session = requests.Session()
        session.headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en,en-US;q=0.9",
        }

        r = session.get("https://www.netflix.com/browse", cookies=cookies)

        if not re.search(BUILD_REGEX, r.text):
            print(
                "cannot get BUILD_IDENTIFIER from the cookies you saved from the browser..."
            )
            sys.exit()

        return re.search(BUILD_REGEX, r.text).group(1)

    def save(self, cookies, build):
        cookie_data = {}
        for name, value in cookies.items():
            cookie_data[name] = [value, 0]
        logindata = {"BUILD_IDENTIFIER": build, "cookies": cookie_data}
        with open(self.config["cookies_file"], "w", encoding="utf8") as f:
            f.write(json.dumps(logindata, indent=4))
            f.close()
        os.remove(self.config["cookies_txt"])

    def read_userdata(self):
        cookies = None
        build = None

        if not os.path.isfile(self.config["cookies_file"]):
            try:
                cj = MozillaCookieJar(self.config["cookies_txt"])
                cj.load()
            except Exception:
                print("invalid netscape format cookies file")
                sys.exit()

            cookies = dict()

            for cookie in cj:
                cookies[cookie.name] = cookie.value

            build = self.get_build(cookies)
            self.save(cookies, build)

        with open(self.config["cookies_file"], "rb") as f:
            content = f.read().decode("utf-8")

        if "NetflixId" not in content:
            self.logger.warning("(Some) cookies expired, renew...")
            return cookies, build

        jso = json.loads(content)
        build = jso["BUILD_IDENTIFIER"]
        cookies = jso["cookies"]
        for cookie in cookies:
            cookie_data = cookies[cookie]
            value = cookie_data[0]
            if cookie != "flwssn":
                cookies[cookie] = value
        if cookies.get("flwssn"):
            del cookies["flwssn"]

        return cookies, build

    def shakti_api(self, nfid):
        url = f"https://www.netflix.com/api/shakti/{self.build}/metadata"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "es,ca;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "www.netflix.com",
            "Pragma": "no-cache",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
            "X-Netflix.browserName": "Chrome",
            "X-Netflix.browserVersion": "79",
            "X-Netflix.clientType": "akira",
            "X-Netflix.esnPrefix": "NFCDCH-02-",
            "X-Netflix.osFullName": "Windows 10",
            "X-Netflix.osName": "Windows",
            "X-Netflix.osVersion": "10.0",
            "X-Netflix.playerThroughput": "1706",
            "X-Netflix.uiVersion": self.build,
        }

        params = {
            "movieid": nfid,
            "drmSystem": "widevine",
            "isWatchlistEnabled": "false",
            "isShortformEnabled": "false",
            "isVolatileBillboardsEnabled": "false",
            "languages": self.config["metada_language"],
        }

        while True:
            resp = requests.get(
                url=url, headers=headers, params=params, cookies=self.cookies
            )

            if resp.status_code == 401:
                self.logger.warning("401 Unauthorized, cookies is invalid.")
            elif resp.text.strip() == "":
                self.logger.error(
                    "title is not available in your Netflix region.")
                exit(-1)

            try:
                t = resp.json()["video"]["type"]
                return resp.json()
            except Exception:
                os.remove(self.config["cookies_file"])
                self.logger.warning(
                    "Error getting metadata: Cookies expired\nplease fetch new cookies.txt"
                )
                exit(-1)

    def main(self):
        self.nfID = '81498937'
        self.cookies, self.build = self.read_userdata()
        data = self.shakti_api(str(self.nfID))
        self.logger.info("Metadata: {}".format(data))
