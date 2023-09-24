#!/usr/bin/python3
# coding: utf-8

"""
This module is to login Disney+
"""

import logging
import re
import json
import sys
from configs.config import user_agent
from utils.helper import get_locale
from utils.proxy import get_ip_info


class Login(object):
    """
    DisneyPlus login authentication, retrieve access_token
    """

    def __init__(self, email, password, locale, config, session):
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, locale)

        self.email = email.strip()
        self.password = password.strip()
        self.config = config

        location = get_ip_info()['loc'].split(',')
        self.latitude = location[0]
        self.longitude = location[1]
        self.session = session

    def client_info(self):
        res = self.session.get(self.config['api']['login_page'], timeout=5)
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
        res = self.session.post(url=self.config['api']['devices'],
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
            url=self.config['api']['token'], headers=header, data=postdata)

        if res.status_code == 200:
            access_token = res.json()['access_token']
            self.logger.debug("access_token: %s", access_token)
            return access_token

        if 'unreliable-location' in str(res.text):
            self.logger.error(
                "Make sure you use NL proxy/vpn, or your proxy/vpn is blacklisted.")
            sys.exit(1)
        else:
            try:
                self.logger.error("\nError: %s", res.json()[
                                  'errors']['error_description'])
                sys.exit(0)
            except Exception:
                self.logger.error("\nError: %s", res.text)
                sys.exit(0)

    def login(self, access_token):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': user_agent,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        data = {'email': self.email, 'password': self.password}
        res = self.session.post(
            url=self.config['api']['login'], data=json.dumps(data), headers=headers)
        if res.status_code == 200:
            id_token = res.json()['id_token']
            self.logger.debug("id_token: %s", id_token)
            return id_token

        try:
            self.logger.error("\nError: %s", res.json()['errors'])
            sys.exit(0)
        except Exception:
            self.logger.error("\nError: %s", res.text)
            sys.exit(0)

    def grant(self, id_token, access_token):

        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': user_agent,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        data = {'id_token': id_token}

        res = self.session.post(
            url=self.config['api']['grant'], data=json.dumps(data), headers=headers)
        if res.ok:
            return res.json()['assertion']
        else:
            self.logger.error(res.text)
            sys.exit(1)

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
            url=self.config['api']['token'], headers=header, data=postdata)

        if res.status_code == 200:
            self.logger.debug(res.json())
            access_token = res.json()['access_token']
            self.logger.debug("access_token: %s", access_token)
            # expires_in = res.json()['expires_in']
            refresh_token = res.json()['refresh_token']
            # return access_token
            return access_token, refresh_token
        try:
            self.logger.error("\nError: %s", res.json()['errors'])
            sys.exit(0)
        except Exception:
            self.logger.error("\nError: %s", res.text)
            sys.exit(0)

    def get_profile_name(self, client_id, token):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {token}',
            'content-type': 'application/json; charset=UTF-8',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': user_agent,
            'x-bamsdk-client-id': client_id,
            'x-bamsdk-platform': 'macintosh',
            'x-bamsdk-version': '3.10',
        }

        res = self.session.get(
            url=self.config['api']['current_account'], headers=headers, timeout=5)

        if res.ok:
            self.logger.debug(res.json())
            user = res.json()
            profile = dict()
            profile['name'] = user['activeProfile']['profileName']
            profile['language'] = user['activeProfile']['attributes']['languagePreferences']['appLanguage']

            self.logger.info(
                self._("\nSuccessfully logged in. Welcome %s!"), profile['name'])

            return profile
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_region(self, token):
        headers = {
            "Accept": "application/vnd.session-service+json; version=1",
            "Authorization": token,
            "Content-Type": "application/json",
            'User-Agent': user_agent
        }

        session_url = self.config['api']['session']

        res = self.session.get(url=session_url, headers=headers, timeout=5)
        if res.ok:
            return res.json()['location']['country_code']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_auth_token(self):
        client_id, client_apikey = self.client_info()
        assertion = self.assertion(client_apikey)
        access_token = self.access_token(client_apikey, assertion)
        id_token = self.login(access_token)
        user_assertion = self.grant(id_token, access_token)
        final_access_token, refresh_token = self.final_token(
            user_assertion, client_apikey)
        profile = self.get_profile_name(client_id, final_access_token)
        region = self.get_region(final_access_token)
        profile['region'] = region
        return profile, final_access_token
