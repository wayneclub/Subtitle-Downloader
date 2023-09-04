#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from meWATCH
"""

import os
import platform
import sys
from configs.config import credentials, user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_all_languages, get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.service import Service


class MeWatch(Service):
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
            sys.exit(1)

    def get_subtitle(self, media_info, folder_path, filename):

        subtitle_list = next((channel['subtitlesCollection'] for channel in media_info
                             if channel.get('subtitlesCollection') and len(channel['subtitlesCollection']) > 0), None)

        subtitles = []
        lang_paths = set()
        if subtitle_list:
            available_languages = set()

            for sub in subtitle_list:
                sub_lang = get_language_code(sub['languageCode'])
                available_languages.add(sub_lang)
                if sub_lang in self.subtitle_language:
                    if len(lang_paths) > 1:
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

    def login(self):
        """Login and get user token"""

        headers = {
            'content-type': 'application/json',
            'authority': 'www.mewatch.sg',
            'user-agent': user_agent,
            'referer': 'https://www.mewatch.sg/signin',
        }

        payload = {
            'username': credentials[self.platform]['email'].strip(),
            'password': credentials[self.platform]['password'].strip(),
            'id': self.config['device_id'],
            'os': platform.system(),
            'browser': 'Chrome'
        }

        cookies = {
            'UID': self.config['device_id'],
        }

        res = self.session.post(
            url=self.config['api']['login'], headers=headers, json=payload, cookies=cookies, timeout=5)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
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
        token = self.get_token()
        user_token = self.login()
        token_list = self.get_access_token(token=token, user_token=user_token)
        self.access_token = next((token['value'] for token in token_list
                                  if token['refreshable'] is True and token['type'] == 'UserProfile'), None)

        conetent_id = os.path.basename(self.url).split('-')[-1]

        if '/movie' in self.url:
            title_url = self.config['api']['movies'].format(
                conetent_id=conetent_id)
            res = self.session.get(url=title_url, timeout=5)
            if res.ok:
                self.movie_metadata(res.json())
            else:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            episodes_url = self.config['api']['series'].format(
                conetent_id=conetent_id)
            res = self.session.get(url=episodes_url, timeout=5)
            if res.ok:
                data = res.json()
                if data.get('show'):
                    data = data['show']
                self.series_metadata(data)
            else:
                self.logger.error(res.text)
                sys.exit(1)
