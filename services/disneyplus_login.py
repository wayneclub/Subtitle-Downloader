'''
This module is to Login Disney+
'''

import logging
import re
import json
import requests


class Login(object):
    def __init__(self, email, password):
        self.logger = logging.getLogger(__name__)
        self.email = email
        self.password = password
        self.web_page = 'https://www.disneyplus.com/login'
        self.devices_url = 'https://global.edge.bamgrid.com/devices'
        self.login_url = 'https://global.edge.bamgrid.com/idp/login'
        self.token_url = 'https://global.edge.bamgrid.com/token'
        self.grant_url = 'https://global.edge.bamgrid.com/accounts/grant'
        self.current_account_url = 'https://global.edge.bamgrid.com/accounts/me'

        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        self.session = requests.Session()

    def client_info(self):
        res = self.session.get(self.web_page)
        match = re.search('window.server_path = ({.*});', res.text)
        data = json.loads(match.group(1))
        client_id = data['sdk']['clientId']
        client_apikey = data['sdk']['clientApiKey']
        return client_id, client_apikey

    def assertion(self, client_apikey):

        postdata = {
            'applicationRuntime': 'chrome',
            'attributes': {},
            'deviceFamily': 'browser',
            'deviceProfile': 'macosx'
        }

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}
        res = self.session.post(url=self.devices_url,
                                headers=header, json=postdata)
        assertion = res.json()['assertion']

        return assertion

    def access_token(self, client_apikey, assertion_):

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}

        postdata = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'latitude': '0',
            'longitude': '0',
            'platform': 'browser',
            'subject_token': assertion_,
            'subject_token_type': 'urn:bamtech:params:oauth:token-type:device'
        }

        res = self.session.post(
            url=self.token_url, headers=header, data=postdata)

        if res.status_code == 200:
            access_token = res.json()['access_token']
            return access_token

        if 'unreliable-location' in str(res.text):
            print('Make sure you use NL proxy/vpn, or your proxy/vpn is blacklisted.')
            exit()
        else:
            try:
                print('Error: ' + str(res.json()
                                      ['errors']['error_description']))
                exit()
            except Exception:
                print('Error: ' + str(res.text))
                exit()

    def login(self, access_token):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-platform': 'macosx',
            'x-bamsdk-version': '3.10',
        }

        data = {'email': self.email, 'password': self.password}
        res = self.session.post(
            url=self.login_url, data=json.dumps(data), headers=headers)
        if res.status_code == 200:
            id_token = res.json()['id_token']
            return id_token

        try:
            print('Error: ' + str(res.json()['errors']))
            exit()
        except Exception:
            print('Error: ' + str(res.text))
            exit()

    def grant(self, id_token, access_token):

        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json; charset=UTF-8',
            'Origin': 'https://www.disneyplus.com',
            'Referer': 'https://www.disneyplus.com/login/password',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-platform': 'macosx',
            'x-bamsdk-version': '3.10',
        }

        data = {'id_token': id_token}

        res = self.session.post(
            url=self.grant_url, data=json.dumps(data), headers=headers)
        assertion = res.json()['assertion']

        return assertion

    def final_token(self, subject_token, client_apikey):

        header = {'authorization': f'Bearer {client_apikey}',
                  'Origin': 'https://www.disneyplus.com'}

        postdata = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'latitude': '0',
            'longitude': '0',
            'platform': 'browser',
            'subject_token': subject_token,
            'subject_token_type': 'urn:bamtech:params:oauth:token-type:account'
        }

        res = self.session.post(
            url=self.token_url, headers=header, data=postdata)

        if res.status_code == 200:
            access_token = res.json()['access_token']
            # expires_in = res.json()['expires_in']
            return access_token

        try:
            print('Error: ' + str(res.json()['errors']))
            exit()
        except Exception:
            print('Error: ' + str(res.text))
            exit()

    def get_auth_token(self):

        client_id, client_apikey = self.client_info()
        assertion = self.assertion(client_apikey)
        access_token = self.access_token(client_apikey, assertion)
        id_token = self.login(access_token)
        user_assertion = self.grant(id_token, access_token)
        token = self.final_token(user_assertion, client_apikey)

        self.get_profile_name(client_id, token)

        return token

    def get_profile_name(self, client_id, token):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'authorization': f'Bearer {token}',
            'content-type': 'application/json; charset=UTF-8',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.user_agent,
            'x-bamsdk-client-id': client_id,
            'x-bamsdk-platform': 'macosx',
            'x-bamsdk-version': '3.10',
        }

        res = self.session.get(
            url=self.current_account_url, headers=headers)

        if res.status_code == 200:
            profile_name = res.json()['activeProfile']['profileName']
            self.logger.info(
                '\n登入成功，歡迎 %s', profile_name)
