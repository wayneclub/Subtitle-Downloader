#!/usr/bin/python3
# coding: utf-8

"""
This module is to login Disney+
"""

import logging
import re
import json
from getpass import getpass
import requests
from common.utils import get_locale, get_ip_location, get_user_agent


class Login(object):
    def __init__(self, email, password, locale):
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, locale)
        self.email = email
        self.password = password

        location = get_ip_location()['loc'].split(',')

        self.latitude = location[0]
        self.longitude = location[1]

        self.api = {
            # 'login_page': 'https://www.disneyplus.com/login',
            'login_page': 'https://www.disneyplus.com/ja-jp/login',
            'devices': 'https://global.edge.bamgrid.com/devices',
            'login': 'https://global.edge.bamgrid.com/idp/login',
            'token': 'https://global.edge.bamgrid.com/token',
            'grant': 'https://global.edge.bamgrid.com/accounts/grant',
            'current_account': 'https://global.edge.bamgrid.com/accounts/me'
        }

        self.user_agent = get_user_agent()
        self.session = requests.Session()

    def client_info(self):
        res = self.session.get(self.api['login_page'])
        match = re.search('window.server_path = ({.*});', res.text)
        data = json.loads(match.group(1))
        client_id = data['sdk']['clientId']
        client_apikey = data['sdk']['clientApiKey']
        self.logger.debug("client_id: %s\nclient_apikey: %s",
                          client_id, client_apikey)
        return client_id, client_apikey

    def assertion(self, client_apikey):

        postdata = {
            'applicationRuntime': 'chrome',
            'attributes': {},
            'deviceFamily': 'browser',
            'deviceProfile': 'macintosh'
        }

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}
        res = self.session.post(url=self.api['devices'],
                                headers=header, json=postdata)
        assertion = res.json()['assertion']
        self.logger.debug("assertion: %s", assertion)
        return assertion

    def access_token(self, client_apikey, assertion_):

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}

        postdata = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'platform': 'browser',
            'subject_token': assertion_,
            'subject_token_type': 'urn:bamtech:params:oauth:token-type:device'
        }

        res = self.session.post(
            url=self.api['token'], headers=header, data=postdata)

        if res.status_code == 200:
            access_token = res.json()['access_token']
            self.logger.debug("access_token: %s", access_token)
            return access_token

        if 'unreliable-location' in str(res.text):
            self.logger.info(
                "Make sure you use NL proxy/vpn, or your proxy/vpn is blacklisted.")
            exit(0)
        else:
            try:
                self.logger.error("Error: %s", res.json()[
                                  'errors']['error_description'])
                exit(0)
            except Exception:
                self.logger.error("Error: %s", res.text)
                exit(0)

    def login(self, access_token):

        if self.email and self.password:
            email = self.email.strip()
            password = self.password.strip()
        else:
            email = input(self._("Disney+ email: "))
            password = getpass(self._("Disney+ password: "))

        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        data = {'email': email, 'password': password}
        res = self.session.post(
            url=self.api['login'], data=json.dumps(data), headers=headers)
        if res.status_code == 200:
            id_token = res.json()['id_token']
            self.logger.debug("id_token: %s", id_token)
            return id_token

        try:
            self.logger.error("Error: %s", res.json()['errors'])
            exit(0)
        except Exception:
            self.logger.error("Error: %s", res.text)
            exit(0)

    def grant(self, id_token, access_token):

        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        data = {'id_token': id_token}

        res = self.session.post(
            url=self.api['grant'], data=json.dumps(data), headers=headers)
        assertion = res.json()['assertion']

        return assertion

    def final_token(self, subject_token, client_apikey):

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}

        postdata = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'platform': 'browser',
            'subject_token': subject_token,
            'subject_token_type': 'urn:bamtech:params:oauth:token-type:account'
        }

        res = self.session.post(
            url=self.api['token'], headers=header, data=postdata)

        if res.status_code == 200:
            self.logger.debug(res.json())
            access_token = res.json()['access_token']
            self.logger.debug("access_token: %s", access_token)
            # expires_in = res.json()['expires_in']
            refresh_token = res.json()['refresh_token']
            # return access_token
            return access_token, refresh_token
        try:
            self.logger.error("Error: %s", res.json()['errors'])
            exit(0)
        except Exception:
            self.logger.error("Error: %s", res.text)
            exit(0)

    def get_profile_name(self, client_id, token):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {token}',
            'content-type': 'application/json; charset=UTF-8',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-client-id': client_id,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        res = self.session.get(
            url=self.api['current_account'], headers=headers)

        if res.status_code == 200:
            self.logger.debug(res.json())
            user = res.json()
            profile = dict()
            profile['name'] = user['activeProfile']['profileName']
            profile['language'] = user['activeProfile']['attributes']['languagePreferences']['appLanguage']
            profile['country'] = user['attributes']['locations']['registration']['geoIp']['country']

            self.logger.info(
                self._("\nSuccessfully logged in. Welcome %s!"), profile['name'])

            return profile

    def get_new_access(self, client_id, client_apikey, refresh_token):
        header = {
            'authorization': f'Bearer {client_apikey}',
            'Origin': 'https://www.disneyplus.com',
            'User-Agent': self.user_agent,
            'x-bamsdk-client-id': client_id,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-platform-id': 'browser'
        }

        postdata = {"query": "mutation refreshToken($input: RefreshTokenInput!) {\n            refreshToken(refreshToken: $input) {\n                activeSession {\n                    sessionId\n                }\n            }\n        }", "variables": {
            "input": {"refreshToken": refresh_token}}}

        res = self.session.post(
            url='https://disney.api.edge.bamgrid.com/graph/v1/device/graphql', headers=header, json=postdata)

        print(res.text)
        if res.status_code == 200:
            access_token = res.json(
            )['extensions']['sdk']['token']['accessToken']
            self.logger.debug("access_token: %s", access_token)
            return access_token

    def get_auth_token(self):
        client_id, client_apikey = self.client_info()
        assertion = self.assertion(client_apikey)
        access_token = self.access_token(client_apikey, assertion)
        id_token = self.login(access_token)
        user_assertion = self.grant(id_token, access_token)
        final_access_token, refresh_token = self.final_token(
            user_assertion, client_apikey)
        profile = self.get_profile_name(client_id, final_access_token)
        return profile, final_access_token
