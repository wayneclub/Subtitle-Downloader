#!/usr/bin/python3
# coding: utf-8

"""
This module is to save and read cookies
"""
import sys
import logging
import os
import re
import orjson


class Cookies(object):
    def __init__(self, credential):
        self.logger = logging.getLogger(__name__)
        self.credential = credential
        self.cookies = None

    def load_cookies(self, client_id):
        cookies = None
        if not os.path.isfile(self.credential['cookies_file']):
            if not os.path.exists(self.credential['cookies_txt']):
                self.logger.error("\nPlease put %s in [configs/cookies] and re-genertate cookie files.",
                                  os.path.basename(self.credential['cookies_txt']))
                sys.exit(1)

            cookies = dict()

            cookies = {}
            with open(self.credential['cookies_txt'], 'r') as file:
                for line in file:
                    if not re.match(r'^\#', line):
                        line_fields = line.strip().split('\t')
                        if len(line_fields) > 6:
                            cookies[line_fields[5]] = line_fields[6]

            self.save_cookies(cookies)

        with open(self.credential['cookies_file'], 'rb') as file:
            content = file.read().decode('utf-8')

        if client_id not in content:
            self.logger.warning(
                "\nMissing \"%s\" in %s.\nPlease login to streaming services and renew cookies...",
                client_id,
                os.path.basename(self.credential['cookies_file']))
            os.remove(self.credential['cookies_file'])
            sys.exit()

        cookies = orjson.loads(content)['cookies']
        for cookie in cookies:
            cookie_data = cookies[cookie]
            value = cookie_data[0]
            if cookie != 'flwssn':
                cookies[cookie] = value
        if cookies.get('flwssn'):
            del cookies['flwssn']

        self.cookies = cookies

    def save_cookies(self, cookies, build_id=""):
        cookie_data = {}
        for name, value in cookies.items():
            cookie_data[name] = [value, 0]

        if build_id:
            cookies = {'BUILD_IDENTIFIER': build_id, 'cookies': cookie_data}
        else:
            cookies = {'cookies': cookie_data}

        with open(self.credential['cookies_file'], 'wb') as file:
            file.write(orjson.dumps(cookies, option=orjson.OPT_INDENT_2))
            file.close()

        if os.path.exists(self.credential['cookies_txt']):
            os.remove(self.credential['cookies_txt'])

    def get_cookies(self):
        return self.cookies
