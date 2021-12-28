#!/usr/bin/python3
#coding: utf-8

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
import requests
from common.utils import http_request, HTTPMethod, download_file, pretty_print_json, convert_subtitle


class HBOGO(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url
        self.username = args.email
        self.password = args.password

        if args.output:
            self.output = args.output
        else:
            self.output = os.getcwd()
        if args.season:
            self.download_season = int(args.season)
        else:
            self.download_season = None

        self.subtitle_language = args.subtitle_language

        self.language_list = []
        self.device_id = str(uuid.uuid4())
        self.territory = ""
        self.channel_partner_id = ""
        self.session_token = ""
        self.multi_profile_id = ""

        self.session = requests.Session()

        self.language_code = {
            'en': 'ENG',
            'zh-Hant': 'CHN',
            'zh-Hans': 'CHZ',
            'ms': 'MAL',
            'th': 'THA'
        }

    def get_language_code(self, lang, reverse=False):
        language_code_reverse = dict(
            zip(self.language_code.values(), self.language_code.keys()))
        if reverse:
            return language_code_reverse.get(lang) if language_code_reverse.get(lang) else 'en'
        else:
            return self.language_code.get(lang) if self.language_code.get(lang) else 'ENG'

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'
        elif self.subtitle_language == 'all':
            self.subtitle_language = ','.join(list(self.language_code.keys()))

        if ',' not in self.subtitle_language:
            self.language_list = [
                self.get_language_code(self.subtitle_language)]
        else:
            self.language_list = [self.get_language_code(
                language) for language in self.subtitle_language.split(',')]

    def get_territory(self):
        geo_url = f'https://api2.hbogoasia.com/v1/geog?lang=zh-Hant&version=0&bundleId={urlparse(self.url).netloc}'

        response = http_request(session=self.session,
                                url=geo_url, method=HTTPMethod.GET)
        if 'territory' in response:
            self.territory = response['territory']
        else:
            self.logger.info('HBOGO Asia 未在此區提供服務')
            exit()

    def login(self):

        if self.username and self.password:
            username = self.username
            password = self.password
        else:
            username = input('輸入帳號：')
            password = getpass('輸入密碼（不顯示）：')

        payload = {
            "contactPassword": password.strip(),
            "contactUserName": username.strip(),
            "deviceDetails": {
                "deviceName": platform.system(),
                "deviceType": "COMP",
                "modelNo": self.device_id,
                "serialNo": self.device_id,
                "appType": "Web",
                "status": "Active"
            }
        }

        auth_url = 'https://api2.hbogoasia.com/v1/hbouser/login?lang=zh-Hant'
        kwargs = {'json': payload}

        response = http_request(session=self.session,
                                url=auth_url, method=HTTPMethod.POST, kwargs=kwargs)
        self.logger.debug('\n%s\n', pretty_print_json(response))
        self.channel_partner_id = response['channelPartnerID']
        self.session_token = response['sessionToken']
        # self.multi_profile_id = response['multiProfileId']
        user_name = response['name']
        self.logger.info('\n登入成功，歡迎 %s', user_name.strip())

    def remove_device(self):
        delete_url = 'https://api2.hbogoasia.com/v1/hbouser/device?lang=zh-Hant'
        payload = {
            "sessionToken": self.session_token,
            "multiProfileId": "0",
            "serialNo": self.device_id
        }
        kwargs = {'json': payload}
        response = http_request(session=self.session,
                                url=delete_url, method=HTTPMethod.DELETE, kwargs=kwargs)
        self.logger.debug('\n%s\n', pretty_print_json(response))

    def download_subtitle(self):
        if '/sr' in self.url:

            series_id_regex = re.search(
                r'https:\/\/www\.hbogoasia.+\/sr(\d+)', self.url)
            if series_id_regex:
                series_id = series_id_regex.group(1)
                series_url = f'https://api2.hbogoasia.com/v1/tvseason/list?parentId={series_id}&territory={self.territory}'
            else:
                self.logger.error('找不到影集，請輸入正確網址')
                exit(1)

            season_list = http_request(session=self.session,
                                       url=series_url, method=HTTPMethod.GET)['results']

            title = next(title['name'] for title in season_list[0]
                         ['metadata']['titleInformations'] if title['lang'] == 'CHN')

            drama_name = re.sub(r'S\d+', '', title).strip()
            self.logger.info('\n%s 共有：%s 季', drama_name, len(season_list))

            for season in season_list:
                season_index = season['seasonNumber']
                if not self.download_season or season_index == self.download_season:
                    season_url = f"https://api2.hbogoasia.com/v1/tvepisode/list?parentId={season['contentId']}&territory={self.territory}"
                    season_name = str(season_index).zfill(2)

                    folder_path = os.path.join(
                        self.output, f'{drama_name}.S{season_name}')
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    episode_list = http_request(session=self.session,
                                                url=season_url, method=HTTPMethod.GET)
                    episode_num = episode_list['total']

                    self.logger.info(
                        '\n第 %s 季 共有：%s 集\t下載全集\n---------------------------------------------------------------', season_index, episode_num)

                    lang_paths = set()
                    for episode in episode_list['results']:
                        episode_index = episode['episodeNumber']
                        content_id = episode['contentId']

                        file_name = f"{drama_name}.S{season_name}E{str(episode_index).zfill(2)}.WEB-DL.HBOGO.vtt"

                        lang_paths = self.parse_subtitle(
                            content_id, episode, folder_path, file_name)

                    for lang_path in lang_paths:
                        convert_subtitle(lang_path)

                    convert_subtitle(folder_path, 'hbogo')
        else:
            content_id = os.path.basename(self.url)
            movie_url = f'https://api2.hbogoasia.com/v1/movie?contentId={content_id}&territory={self.territory}'

            movie = http_request(session=self.session,
                                 url=movie_url, method=HTTPMethod.GET)

            title = next(title['name'] for title in movie['metadata']
                         ['titleInformations'] if title['lang'] == 'CHN').strip()
            self.logger.info('\n%s', title)

            release_year = movie['metadata']['releaseDate'][:4]

            folder_path = os.path.join(self.output, f'{title}.{release_year}')
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            file_name = f'{title}.{release_year}.WEB-DL.HBOGO.vtt'

            self.logger.info(
                '\n下載字幕\n---------------------------------------------------------------')

            self.parse_subtitle(content_id, movie, folder_path, file_name)
            convert_subtitle(folder_path, 'hbogo')

    def parse_subtitle(self, content_id, video, folder_path, file_name):
        video_url = f'https://api2.hbogoasia.com/v1/asset/playbackurl?territory={self.territory}&contentId={content_id}&sessionToken={self.session_token}&channelPartnerID={self.channel_partner_id}&operatorId=SIN&lang=zh-Hant'

        response = http_request(session=self.session,
                                url=video_url, method=HTTPMethod.GET)

        mpd_url = response['playbackURL']

        lang_paths = set()

        category = video['metadata']['categories'][0]

        for media in video['materials']:
            if media['type'] == 'subtitle':
                if media['lang'] in self.language_list:
                    if len(self.language_list) > 1:
                        if category == 'SERIES':
                            lang_folder_path = os.path.join(
                                folder_path, self.get_language_code(media['lang'], True))
                        else:
                            lang_folder_path = folder_path
                    else:
                        lang_folder_path = folder_path
                    lang_paths.add(lang_folder_path)
                    subtitle_file = media['href']
                    lang_code = Path(
                        subtitle_file).stem.replace(content_id, '')

                    subtitle_file_name = file_name.replace(
                        '.vtt', f".{self.get_language_code(media['lang'], True)}.vtt")

                    subtitle_link = mpd_url.replace(
                        os.path.basename(mpd_url), f"subtitles/{lang_code}/{subtitle_file}")

                    os.makedirs(lang_folder_path,
                                exist_ok=True)
                    download_file(subtitle_link, os.path.join(
                        lang_folder_path, subtitle_file_name))
        return lang_paths

    def main(self):
        self.get_language_list()
        self.logger.debug(
            '\nDownload language: %s\n', self.language_list)
        self.get_territory()
        self.login()
        self.download_subtitle()
        self.remove_device()
