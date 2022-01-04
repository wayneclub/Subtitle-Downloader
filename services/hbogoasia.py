#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from HBOGO Asia
"""

import re
import os
import shutil
import platform
import logging
import uuid
from getpass import getpass
from pathlib import Path
from urllib.parse import urlparse
from common.utils import get_locale, Platform, http_request, HTTPMethod, pretty_print_json, download_files
from common.subtitle import convert_subtitle
from services.service import Service


class HBOGOAsia(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)
        self.username = args.email
        self.password = args.password

        self.subtitle_language = args.subtitle_language

        self.language_list = ()
        self.device_id = str(uuid.uuid4())
        self.territory = ""
        self.channel_partner_id = ""
        self.session_token = ""
        self.multi_profile_id = ""

        self.api = {
            'geo': 'https://api2.hbogoasia.com/v1/geog?lang=zh-Hant&version=0&bundleId={bundle_id}',
            'login': 'https://api2.hbogoasia.com/v1/hbouser/login?lang=zh-Hant',
            'device': 'https://api2.hbogoasia.com/v1/hbouser/device?lang=zh-Hant',
            'tvseason': 'https://api2.hbogoasia.com/v1/tvseason/list?parentId={parent_id}&territory={territory}',
            'tvepisode': 'https://api2.hbogoasia.com/v1/tvepisode/list?parentId={parent_id}&territory={territory}',
            'movie': 'https://api2.hbogoasia.com/v1/movie?contentId={content_id}&territory={territory}',
            'playback': 'https://api2.hbogoasia.com/v1/asset/playbackurl?territory={territory}&contentId={content_id}&sessionToken={session_token}&channelPartnerID={channel_partner_id}&operatorId=SIN&lang=zh-Hant'
        }

    def get_language_code(self, lang):
        language_code = {
            'ENG': 'en',
            'CHN': 'zh-Hant',
            'CHC': 'zh-Hant',
            'CHZ': 'zh-Hans',
            'MAL': 'ms',
            'THA': 'th',
            'IND': 'id',
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def get_territory(self):
        geo_url = self.api['geo'].format(bundle_id=urlparse(self.url).netloc)
        response = http_request(session=self.session,
                                url=geo_url, method=HTTPMethod.GET)
        if 'territory' in response:
            self.territory = response['territory']
            self.logger.debug(self.territory)
        else:
            self.logger.info(
                self._("\nOut of service!"))
            exit(0)

    def login(self):

        if self.username and self.password:
            username = self.username
            password = self.password
        else:
            username = input(self._("HBOGO Asia username: "))
            password = getpass(self._("HBOGO Asia password: "))

        payload = {
            'contactPassword': password.strip(),
            'contactUserName': username.strip(),
            'deviceDetails': {
                'deviceName': platform.system(),
                'deviceType': "COMP",
                'modelNo': self.device_id,
                'serialNo': self.device_id,
                'appType': 'Web',
                'status': 'Active'
            }
        }

        auth_url = self.api['login']
        kwargs = {'json': payload}

        response = http_request(session=self.session,
                                url=auth_url, method=HTTPMethod.POST, kwargs=kwargs)
        self.logger.debug('\n%s\n', pretty_print_json(response))
        self.channel_partner_id = response['channelPartnerID']
        self.session_token = response['sessionToken']
        # self.multi_profile_id = response['multiProfileId']
        user_name = response['name']
        self.logger.info(
            self._("\nSuccessfully logged in. Welcome %s!"), user_name.strip())

    def remove_device(self):
        delete_url = self.api['device']
        payload = {
            "sessionToken": self.session_token,
            "multiProfileId": "0",
            "serialNo": self.device_id
        }
        kwargs = {'json': payload}
        response = http_request(session=self.session,
                                url=delete_url, method=HTTPMethod.DELETE, kwargs=kwargs)
        self.logger.debug('\n%s\n', pretty_print_json(response))

    def get_all_languages(self, data):
        available_languages = tuple([self.get_language_code(
            media['lang']) for media in data['materials'] if media['type'] == 'subtitle'])

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            exit(0)

    def download_subtitle(self):
        if '/sr' in self.url:

            series_id_regex = re.search(
                r'https:\/\/www\.hbogoasia.+\/sr(\d+)', self.url)
            if series_id_regex:
                series_id = series_id_regex.group(1)
                series_url = self.api['tvseason'].format(
                    parent_id=series_id, territory=self.territory)
            else:
                self.logger.error(self._("\nSeries not found!"))
                exit(1)

            season_list = http_request(session=self.session,
                                       url=series_url, method=HTTPMethod.GET)['results']

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
                season_index = season['seasonNumber']
                if not self.download_season or season_index == self.download_season:
                    season_url = self.api['tvepisode'].format(
                        parent_id=season['contentId'], territory=self.territory)
                    self.logger.debug(season_url)
                    season_name = str(season_index).zfill(2)

                    folder_path = os.path.join(
                        self.output, f'{title}.S{season_name}')
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    episode_list = http_request(session=self.session,
                                                url=season_url, method=HTTPMethod.GET)
                    episode_num = episode_list['total']

                    self.logger.info(
                        self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                    languages = set()
                    subtitles = []
                    for episode in episode_list['results']:
                        episode_index = episode['episodeNumber']
                        content_id = episode['contentId']

                        file_name = f'{title}.S{season_name}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.HBOGO}.vtt'

                        self.logger.info(self._("Finding %s ..."), file_name)
                        subs, lang_paths = self.get_subtitle(
                            content_id, episode, folder_path, file_name)
                        subtitles += subs
                        languages = set.union(languages, lang_paths)

                    download_files(subtitles)
                    for lang_path in sorted(languages):
                        convert_subtitle(
                            folder_path=lang_path, lang=self.locale)

                    convert_subtitle(folder_path=folder_path,
                                     ott=Platform.HBOGO, lang=self.locale)
        else:
            content_id = os.path.basename(self.url)
            movie_url = self.api['movie'].format(
                content_id=content_id, territory=self.territory)

            movie = http_request(session=self.session,
                                 url=movie_url, method=HTTPMethod.GET)

            title = next(title['name'] for title in movie['metadata']
                         ['titleInformations'] if title['lang'] == 'CHN').strip()
            self.logger.info("\n%s", title)

            release_year = movie['metadata']['releaseDate'][:4]

            folder_path = os.path.join(self.output, f'{title}.{release_year}')
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            file_name = f'{title}.{release_year}.WEB-DL.{Platform.HBOGO}.vtt'

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

            subtitles = self.get_subtitle(
                content_id, movie, folder_path, file_name)[0]

            download_files(subtitles)
            convert_subtitle(folder_path=folder_path,
                             ott=Platform.HBOGO, lang=self.locale)

    def get_subtitle(self, content_id, data, folder_path, file_name):
        playback_url = self.api['playback'].format(territory=self.territory, content_id=content_id,
                                                   session_token=self.session_token, channel_partner_id=self.channel_partner_id)
        self.logger.debug(playback_url)
        response = http_request(session=self.session,
                                url=playback_url, method=HTTPMethod.GET)

        mpd_url = response['playbackURL']

        category = data['metadata']['categories'][0]

        self.get_all_languages(data)

        lang_paths = set()
        subtitles = []
        for media in data['materials']:
            if media['type'] == 'subtitle':
                self.logger.debug(media)
                sub_lang = self.get_language_code(media['lang'])
                if sub_lang in self.language_list:
                    if len(self.language_list) > 1:
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

                    subtitle_file_name = file_name.replace(
                        '.vtt', f'.{sub_lang}.vtt')

                    subtitle_link = mpd_url.replace(
                        os.path.basename(mpd_url), f'subtitles/{lang_code}/{subtitle_file}')
                    self.logger.debug(subtitle_link)

                    os.makedirs(lang_folder_path,
                                exist_ok=True)
                    subtitle = dict()
                    subtitle['name'] = subtitle_file_name
                    subtitle['path'] = lang_folder_path
                    subtitle['url'] = subtitle_link
                    subtitles.append(subtitle)
        return subtitles, lang_paths

    def main(self):
        self.get_language_list()
        self.get_territory()
        self.login()
        self.download_subtitle()
        self.remove_device()
