#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from meWATCH
"""

import os
import platform
import sys
from base64 import b64encode, b64decode

from bs4 import BeautifulSoup
from configs.config import credentials, user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_all_languages, get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.baseservice import BaseService


class MeWatch(BaseService):
    """
    Service code for meWATCH streaming service (https://www.mewatch.sg/).

    Authorization: Cookies
    """

    GEOFENCE = ['sg']

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.access_token = ''

    def movie_metadata(self, data):
        title = data['title'].strip()
        release_year = data['releaseYear']

        self.logger.info("\n%s (%s)", title, release_year)

        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)
        filename = f"{title}.WEB-DL.{self.platform}.vtt"

        languages = set()
        subtitles = []

        media_info = self.get_media_info(video_id=data['id'])

        subs, lang_paths = self.get_subtitle(
            media_info=media_info, folder_path=folder_path, filename=filename)
        subtitles += subs
        languages = set.union(languages, lang_paths)

        if subtitles:
            self.logger.info(
                self._(
                    "\nDownload: %s\n---------------------------------------------------------------"),
                filename)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

    def series_metadata(self, data):
        title = data['title'].strip()
        self.logger.info(self._("\n%s total: %s season(s)"),
                         title, data['seasons']['size'])

        for season in data['seasons']['items']:
            season_index = season['seasonNumber']
            if not self.download_season or season_index in self.download_season:
                episode_list = []
                episodes_url = self.config['api']['episodes'].format(
                    season_id=season['id'])
                res = self.session.get(url=episodes_url, timeout=5)
                if res.ok:
                    episode_list = res.json()['items']
                else:
                    self.logger.error(res.text)
                    sys.exit(1)

                episode_num = len(episode_list)
                name = rename_filename(
                    f'{title}.S{str(season_index).zfill(2)}')
                folder_path = os.path.join(self.download_path, name)

                if self.last_episode:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num,
                                     season_index)

                    episode_list = [episode_list[-1]]
                else:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num)

                languages = set()
                subtitles = []
                for episode in episode_list:
                    episode_index = episode['episodeNumber']
                    if not self.download_episode or episode_index in self.download_episode:
                        filename = f"{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt"

                        media_info = self.get_media_info(
                            video_id=episode['id'])
                        subs, lang_paths = self.get_subtitle(
                            media_info=media_info, folder_path=folder_path, filename=filename)

                        if not subs:
                            break

                        subtitles += subs
                        languages = set.union(languages, lang_paths)

                self.download_subtitle(
                    subtitles=subtitles, languages=languages, folder_path=folder_path)

    def get_media_info(self, video_id):

        self.session.headers = {
            'user-agent': user_agent,
            'x-authorization': f'Bearer {self.access_token}',
        }
        media_info_url = self.config['api']['videos'].format(
            video_id=video_id)

        res = self.session.get(url=media_info_url, timeout=5)

        if res.ok:
            data = res.json()
            if len(data) > 0:
                self.logger.debug("media_info: %s", data)
                return data
            else:
                self.logger.error(res.text)
        else:
            error = res.json()
            self.logger.error("\nError: %s", error['message'])

    def get_subtitle(self, media_info, folder_path, filename):
        subtitles = []
        lang_paths = set()
        subtitle_list = []
        if media_info:
            subtitle_list = next((channel['subtitlesCollection'] for channel in media_info
                                  if channel.get('subtitlesCollection') and len(channel['subtitlesCollection']) > 0), None)
        if subtitle_list:
            available_languages = set()

            for sub in subtitle_list:
                sub_lang = get_language_code(sub['languageCode'])
                available_languages.add(sub_lang)
                if sub_lang in self.subtitle_language or 'all' in self.subtitle_language:
                    if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                        lang_folder_path = os.path.join(
                            folder_path, sub_lang)
                    else:
                        lang_folder_path = folder_path
                    lang_paths.add(lang_folder_path)

                    os.makedirs(lang_folder_path,
                                exist_ok=True)

                    subtitles.append({
                        'name': filename.replace('.vtt', f'.{sub_lang}.vtt'),
                        'path': lang_folder_path,
                        'url': sub['url']
                    })

            get_all_languages(available_languages=available_languages,
                              subtitle_language=self.subtitle_language, locale_=self.locale)

        else:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))

        return subtitles, lang_paths

    def download_subtitle(self, subtitles, folder_path, languages=None):
        if subtitles:
            download_files(subtitles)
            if languages:
                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def get_token(self):
        """Get default token"""

        headers = {
            'content-type': 'application/json',
            'authority': 'www.mewatch.sg',
            'user-agent': user_agent
        }

        payload = {
            'cookieType': 'Session',
            'deviceId': self.config['device_id'],
        }

        res = self.session.post(
            url=self.config['api']['token'], headers=headers, json=payload, timeout=5)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            return data[0]['value']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_device(self):
        """Login and get user token"""
        print()

    def login(self, token: str):
        """Login and get user token"""

        cookies = {
            'lang': 'en',
            # 'AMCVS_B464317853A9C8390A490D4E%40AdobeOrg': '1',
            # 'ab.storage.deviceId.01d06460-c507-4a14-9be0-cada09002c45': '%7B%22g%22%3A%22aac94842-d06c-0b2c-5750-cc5ba97c4e5c%22%2C%22c%22%3A1696719094567%2C%22l%22%3A1696719716139%7D',
            # 'ab.storage.userId.01d06460-c507-4a14-9be0-cada09002c45': '%7B%22g%22%3A%22555d1165-a831-432e-88b4-667a81fc5b00%22%2C%22c%22%3A1696719716137%2C%22l%22%3A1696719716139%7D',
            # 'ab.storage.sessionId.01d06460-c507-4a14-9be0-cada09002c45': '%7B%22g%22%3A%229916ccff-f36b-1718-b107-2db6441f740c%22%2C%22e%22%3A1696721516145%2C%22c%22%3A1696719716138%2C%22l%22%3A1696719716145%7D',
            # 'ss': '1',
            # 'AMCV_B464317853A9C8390A490D4E%40AdobeOrg': '-1124106680%7CMCIDTS%7C19638%7CMCMID%7C90333747353049229492137118398699740485%7CMCOPTOUT-1696729592s%7CNONE%7CvVersion%7C5.2.0',
            # 'mp_32231f8971e8246b52f0a566df2bbe20_mixpanel': '%7B%22distinct_id%22%3A%20%22mewatch-555d1165-a831-432e-88b4-667a81fc5b00%22%2C%22%24device_id%22%3A%20%2218b0c569bf71212-02abc1882e7d87-18525634-117414-18b0c569bf82821%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22logged_in%22%3A%20false%2C%22sso_id%22%3A%20%22555d1165-a831-432e-88b4-667a81fc5b00%22%2C%22unique_userid%22%3A%20%22mewatch-555d1165-a831-432e-88b4-667a81fc5b00%22%2C%22%24user_id%22%3A%20%22mewatch-555d1165-a831-432e-88b4-667a81fc5b00%22%2C%22__alias%22%3A%20%22mewatch-555d1165-a831-432e-88b4-667a81fc5b00%22%7D',
            # 'sso_id': 'undefined',
        }

        headers = {
            'content-type': 'application/json',
            'authority': 'www.mewatch.sg',
            'user-agent': user_agent,
            'referer': 'https://www.mewatch.sg/signin',
            'x-authorization': token
        }

        payload = {
            'username': credentials[self.platform]['email'].strip(),
            'password': credentials[self.platform]['password'].strip(),
            'id': '7bb6358e-42d2-4c6c-ac68-dbd63685b058',
            'os': 'MacIntel',
            'browser': 'Chrome'
        }

        encode_str = b64encode(str(payload).replace(
            ' ', '').replace("'", '"').encode()).decode()

        payload = {
            'body': encode_str
        }

        res = self.session.post(
            url=self.config['api']['login'], headers=headers, cookies=cookies, json=payload, timeout=5)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            self.logger.info(self._("\nSuccessfully logged in. Welcome!"))
            return data['token']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_access_token(self, token, user_token):
        """Get user profile token"""

        headers = {
            'content-type': 'application/json',
            'authority': 'www.mewatch.sg',
            'referer': 'https://www.mewatch.sg/signin',
            'user-agent': user_agent,
            'x-authorization': f"Bearer {token}"
        }

        payload = {
            'token': user_token,
            'provider': 'Mediacorp',
            'linkAccounts': True,
            'scopes': [
                'Catalog',
                'Commerce',
            ],
            'deviceId': self.config['device_id'],
            'cookieType': 'Persistent'
        }

        res = self.session.post(
            url=self.config['api']['authorization'], headers=headers, json=payload, timeout=5)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            return data
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def main(self):
        if credentials[self.platform]['profile_token']:
            self.access_token = credentials[self.platform]['profile_token'].strip(
            )
        else:
            self.logger.error(
                "Missing profile_token, please follow readme to get the profile token!")
            sys.exit(1)

        content_id = os.path.basename(self.url).split('-')[-1]

        if '/movie' in self.url:
            title_url = self.config['api']['movies'].format(
                content_id=content_id)
            res = self.session.get(url=title_url, timeout=5)
            if res.ok:
                self.movie_metadata(res.json())
            else:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            episodes_url = self.config['api']['series'].format(
                content_id=content_id)
            res = self.session.get(url=episodes_url, timeout=5)
            if res.ok:
                data = res.json()
                if data.get('show'):
                    data = data['show']
                self.series_metadata(data)
            else:
                self.logger.error(res.text)
                sys.exit(1)
