#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from HBOGO Asia
"""

import re
import os
import shutil
import platform
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse
from configs.config import credentials
from utils.io import rename_filename, download_files
from utils.helper import get_language_code, get_locale, get_all_languages
from utils.subtitle import convert_subtitle
from services.baseservice import BaseService


class HBOGOAsia(BaseService):
    """
    Service code for HBOGO Asia streaming service (https://www.hbogoasia.xx).

    Authorization: email & password
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.device_id = str(uuid.uuid4())
        self.origin = f"https://{urlparse(self.url).netloc}"
        self.territory = ""
        self.channel_partner_id = ""
        self.session_token = ""
        self.multi_profile_id = ""

    def get_territory(self):
        geo_url = self.config['api']['geo'].format(
            bundle_id=urlparse(self.url).netloc)
        res = self.session.get(url=geo_url, timeout=5)
        if res.ok:
            data = res.json()
            if 'territory' in data:
                self.territory = data['territory']
                self.logger.debug(self.territory)
            else:
                self.logger.error(
                    self._("\nOut of service!"))
                sys.exit(0)
        else:
            self.logger.error(res.text)

    def login(self):
        """Login and get sessionToken"""

        headers = {
            'origin': self.origin,
            'referer': self.origin
        }

        payload = {
            'contactUserName': credentials[self.platform]['email'].strip(),
            'contactPassword': credentials[self.platform]['password'].strip(),
            'deviceDetails': {
                'deviceName': platform.system(),
                'deviceType': "COMP",
                'modelNo': self.device_id,
                'serialNo': self.device_id,
                'appType': 'Web',
                'status': 'Active'
            }
        }

        auth_url = self.config['api']['login']

        res = self.session.post(url=auth_url, headers=headers, json=payload)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            self.channel_partner_id = data['channelPartnerID']
            self.session_token = data['sessionToken']
            # self.multi_profile_id = response['multiProfileId']
            user_name = data['name']
            self.logger.info(
                self._("\nSuccessfully logged in. Welcome %s!"), user_name.strip())
        else:
            error = res.json()
            self.logger.error("\nError: %s %s",
                              error['code'], error['message'])
            sys.exit(1)

    def remove_device(self):
        """HBOGO limit to 5 devices"""

        delete_url = self.config['api']['device']
        payload = {
            "sessionToken": self.session_token,
            "multiProfileId": "0",
            "serialNo": self.device_id
        }
        res = self.session.delete(url=delete_url, json=payload)
        if res.ok:
            self.logger.debug(res.json())
        else:
            self.logger.error(res.text)

    def movie_subtitle(self, movie_url, content_id):
        res = self.session.get(url=movie_url, timeout=5)

        if res.ok:
            movie = res.json()

            title = next(title['name'] for title in movie['metadata']
                         ['titleInformations'] if title['lang'] == 'CHN').strip()
            release_year = movie['metadata']['releaseDate'][:4]

            self.logger.info("\n%s (%s)", title, release_year)
            title = rename_filename(f'{title}.{release_year}')

            folder_path = os.path.join(self.download_path, title)

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            filename = f'{title}.WEB-DL.{self.platform}.vtt'

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), filename)

            subtitles = self.get_subtitle(
                content_id, movie, folder_path, filename)[0]

            self.download_subtitle(
                subtitles=subtitles, folder_path=folder_path)
        else:
            self.logger.error(res.text)

    def series_subtitle(self, series_url):
        res = self.session.get(url=series_url, timeout=5)
        if res.ok:
            season_list = res.json()['results']

            if len(season_list) > 0:
                if season_list[0]['metadata']['titleInformations'][-1]['lang'] != 'ENG':
                    title = season_list[0]['metadata']['titleInformations'][-1]['name']
                else:
                    title = season_list[0]['metadata']['titleInformations'][0]['name']
                title = re.sub(r'\(第\d+季\)', '', title).strip()
            else:
                self.logger.info(
                    self._("\nThe series isn't available in this region."))

            title = re.sub(r'S\d+', '', title).strip()
            self.logger.info(self._("\n%s total: %s season(s)"),
                             title, len(season_list))

            for season in season_list:
                season_index = int(season['seasonNumber'])
                if not self.download_season or season_index in self.download_season:
                    season_url = self.config['api']['tvepisode'].format(
                        parent_id=season['contentId'], territory=self.territory)
                    self.logger.debug("season url: %s", season_url)

                    name = rename_filename(
                        f'{title}.S{str(season_index).zfill(2)}')
                    folder_path = os.path.join(self.download_path, name)
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    episode_res = self.session.get(url=season_url, timeout=5)
                    if episode_res.ok:
                        episode_list = episode_res.json()
                        episode_num = episode_list['total']

                        self.logger.info(
                            self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                        languages = set()
                        subtitles = []
                        for episode in episode_list['results']:
                            episode_index = int(episode['episodeNumber'])
                            if not self.download_episode or episode_index in self.download_episode:
                                content_id = episode['contentId']

                                filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'

                                self.logger.info(
                                    self._("Finding %s ..."), filename)
                                subs, lang_paths = self.get_subtitle(
                                    content_id, episode, folder_path, filename)
                                subtitles += subs
                                languages = set.union(languages, lang_paths)

                        self.download_subtitle(
                            subtitles=subtitles, languages=languages, folder_path=folder_path)
        else:
            self.logger.error(res.text)

    def get_subtitle(self, content_id, data, folder_path, filename):
        playback_url = self.config['api']['playback'].format(territory=self.territory, content_id=content_id,
                                                             session_token=self.session_token, channel_partner_id=self.channel_partner_id)
        self.logger.debug("playback_url: %s", playback_url)
        res = self.session.get(url=playback_url, timeout=5)

        if res.ok:
            mpd_url = res.json()['playbackURL']

            category = data['metadata']['categories'][0]

            available_languages = tuple([get_language_code(
                media['lang']) for media in data['materials'] if media['type'] == 'subtitle'])

            get_all_languages(available_languages=available_languages,
                              subtitle_language=self.subtitle_language, locale_=self.locale)

            lang_paths = set()
            subtitles = []
            for media in data['materials']:
                if media['type'] == 'subtitle':
                    self.logger.debug(media)
                    sub_lang = get_language_code(media['lang'])
                    if sub_lang in self.subtitle_language or 'all' in self.subtitle_language:
                        if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                            if category == 'SERIES':
                                lang_folder_path = os.path.join(
                                    folder_path, sub_lang)
                            else:
                                lang_folder_path = folder_path
                        else:
                            lang_folder_path = folder_path
                        lang_paths.add(lang_folder_path)
                        subtitle_file = media['href']
                        lang_code = Path(
                            subtitle_file).stem.replace(content_id, '')

                        subtitle_filename = filename.replace(
                            '.vtt', f'.{sub_lang}.vtt')

                        subtitle_link = mpd_url.replace(
                            os.path.basename(mpd_url), f'subtitles/{lang_code}/{subtitle_file}')
                        self.logger.debug(subtitle_link)

                        os.makedirs(lang_folder_path,
                                    exist_ok=True)
                        subtitle = dict()
                        subtitle['name'] = subtitle_filename
                        subtitle['path'] = lang_folder_path
                        subtitle['url'] = subtitle_link
                        subtitles.append(subtitle)
            return subtitles, lang_paths
        else:
            error = res.json()
            self.logger.error("\nError: %s %s",
                              error['code'], error['message'])
            self.remove_device()
            sys.exit(1)

    def download_subtitle(self, subtitles, folder_path, languages=None):
        if subtitles:
            download_files(subtitles)
            if languages:
                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
        self.get_territory()

        self.login()
        if '/sr' in self.url:
            series_id_regex = re.search(
                r'https:\/\/www\.hbogoasia.+\/sr(\d+)', self.url)
            if series_id_regex:
                series_id = series_id_regex.group(1)
                series_url = self.config['api']['tvseason'].format(
                    parent_id=series_id, territory=self.territory)
                self.series_subtitle(series_url)
            else:
                self.logger.error(self._("\nSeries not found!"))
                self.remove_device()
                sys.exit(1)
        else:
            content_id = os.path.basename(self.url)
            movie_url = self.config['api']['movie'].format(
                content_id=content_id, territory=self.territory)
            self.movie_subtitle(movie_url=movie_url, content_id=content_id)
        self.remove_device()
