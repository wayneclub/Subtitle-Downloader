#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from CatchPlay
"""
import logging
import os
import re
import shutil
import sys
import requests
import orjson
from configs.config import Platform
from utils.cookies import Cookies
from utils.helper import get_locale, download_files
from utils.subtitle import convert_subtitle
from services.service import Service


class CatchPlay(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.credential = self.config.credential(Platform.CATCHPLAY)
        self.cookies = Cookies(self.credential)

        self.access_token = ''
        self.api = {
            'auth': 'https://www.catchplay.com/ssr-oauth/getOauth',
            'play': 'https://hp2-api.catchplay.com/me/play',
            'media_info': 'https://vcmsapi.catchplay.com/video/v3/mediaInfo/{video_id}'
        }

    def get_language_code(self, lang):
        language_code = {
            'zh-TW': 'zh-Hant',
            'en': 'en'
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_access_token(self, cookies):

        headers = {
            'user-agent': self.user_agent,
        }

        cookies = requests.utils.cookiejar_from_dict(
            cookies, cookiejar=None, overwrite=True)

        auth_url = self.api['auth']
        res = self.session.get(url=auth_url, headers=headers, cookies=cookies)
        if res.ok:
            if '</html>' in res.text:
                self.logger.error("Out of services!")
                sys.exit(1)
            data = res.json()
            self.logger.debug("User: %s", data)
            self.access_token = data['access_token']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def movie_subtitle(self, data, program_id):
        title = data['apolloState'][f'$Program:{program_id}.title']['local']
        english_title = data['apolloState'][f'$Program:{program_id}.title']['eng']
        release_year = data['apolloState'][f'Program:{program_id}']['releaseYear']
        self.logger.info("\n%s (%s) [%s]", title, english_title, release_year)

        title = self.ripprocess.rename_file_name(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{Platform.CATCHPLAY}.vtt'

        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

        play_video_id, play_token = self.get_vcms_access_token(program_id)
        if play_video_id and play_token:
            self.get_subtitle(
                play_video_id, play_token, folder_path, file_name)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.CATCHPLAY, lang=self.locale)

            if self.output:
                shutil.move(folder_path, self.output)

    def series_subtitle(self, data, program_id):
        main_program = 'getMainProgram({\"id\":\"' + program_id + '\"})'
        main_id = data['apolloState']['ROOT_QUERY'][main_program]['id']
        title = data['apolloState'][f'${main_id}.title']['local']
        english_title = data['apolloState'][f'${main_id}.title']['eng']
        season_num = data['apolloState'][main_id]['totalChildren']

        self.logger.info("\n%s (%s) total: %s season(s)",
                         title, english_title, season_num)

        for season in data['apolloState'][main_id]['children']:
            season_id = season['id']
            season_index = int(
                data['apolloState'][f'${season_id}.title']['short'].replace('S', ''))

            if not self.download_season or season_index in self.download_season:
                title = self.ripprocess.rename_file_name(
                    f'{title}.S{str(season_index).zfill(2)}')
                folder_path = os.path.join(self.download_path, title)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                episode_list = data['apolloState'][season_id]['children']
                episode_num = len(episode_list)
                if self.last_episode:
                    self.logger.info("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------",
                                     season_index,
                                     episode_num,
                                     season_index)
                    episode_list = [episode_list[-1]]
                elif self.download_episode:
                    self.logger.info(
                        "\nSeason %s total: %s episode(s)\tdownload episode: %s\n---------------------------------------------------------------", season_index, episode_num, self.download_episode)
                else:
                    self.logger.info(
                        "\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------", season_index, episode_num)

                for episode_index, episode in enumerate(episode_list, start=1):
                    if not self.download_episode or episode_index in self.download_episode:
                        file_name = f'{title}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.CATCHPLAY}.vtt'
                        episode_id = episode['id'].replace('Program:', '')
                        play_video_id, play_token = self.get_vcms_access_token(
                            episode_id)
                        if play_video_id and play_token:
                            self.get_subtitle(
                                play_video_id, play_token, folder_path, file_name)

                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.CATCHPLAY, lang=self.locale)

                if self.output:
                    shutil.move(folder_path, self.output)

    def get_vcms_access_token(self, video_id):
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {self.access_token}',
            'user-agent': self.user_agent,
        }

        payload = {
            'force': False,
            'programType': 'Video',
            'videoId': video_id,
            'watchType': 'movie'
        }

        play_url = self.api['play']

        res = self.session.post(url=play_url, headers=headers, json=payload)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            play_video_id = data['data']['catchplayVideoId']
            play_token = data['data']['playToken']
            return play_video_id, play_token
        else:
            error_msg = res.json()['message']
            if 'No subscribe record' in error_msg:
                self.logger.error(
                    "Please check your subscription plan, and make sure you are able to watch it online!")
            elif 'Insufficient permission to access' in error_msg:
                self.logger.error(
                    "Please renew the cookies!")
                os.remove(self.credential['cookies_file'])
            else:
                self.logger.error(
                    "Error: %s", error_msg)
            sys.exit(1)

    def get_subtitle(self, play_video_id, play_token, folder_path, file_name):
        headers = {
            'asiaplay-os-type': 'chrome',
            'asiaplay-device-model': 'mac os',
            'asiaplay-app-version': '3.0',
            'authorization': f'Bearer {play_token}',
            'user-agent': self.user_agent,
            'asiaplay-platform': 'desktop',
            'asiaplay-os-version': '97.0.4692',
            'asiaplay-device-type': 'web'
        }

        media_info_url = self.api['media_info'].format(video_id=play_video_id)
        res = self.session.get(url=media_info_url, headers=headers)

        if res.ok:
            data = res.json()
            self.logger.debug('media_info: %s', data)
            if 'subtitleInfo' in data and data['subtitleInfo']:
                lang_paths = set()
                subtitles = []
                for sub in data['subtitleInfo']:
                    sub_lang = self.get_language_code(sub['language'])
                    lang_folder_path = folder_path
                    lang_paths.add(lang_folder_path)
                    subtitle_file_name = file_name.replace(
                        '.vtt', f'.{sub_lang}.vtt')
                    subtitle_link = sub['src']
                    self.logger.debug(subtitle_link)
                    os.makedirs(lang_folder_path,
                                exist_ok=True)
                    subtitle = dict()
                    subtitle['name'] = subtitle_file_name
                    subtitle['path'] = lang_folder_path
                    subtitle['url'] = subtitle_link
                    subtitles.append(subtitle)

                download_files(subtitles)
            else:
                mpd_url = data['videoUrl']
                self.logger.debug('mpd_url: %s', mpd_url)
                os.makedirs(folder_path, exist_ok=True)
                self.ripprocess.download_subtitles_from_mpd(
                    url=mpd_url, title=file_name.replace('.vtt', ''), folder_path=folder_path)
        else:
            self.logger.error(res.text)

    def main(self):
        self.cookies.load_cookies('connect.sid')
        self.get_access_token(self.cookies.get_cookies())
        res = self.session.get(url=self.url)
        if res.ok:
            match = re.search(
                r'<script id=\"__NEXT_DATA__" type=\"application/json\">(.+?)<\/script>', res.text)
            if match:
                data = orjson.loads(match.group(1).strip())[
                    'props']['pageProps']
                program_id = os.path.basename(self.url)
                if data['apolloState'][f'Program:{program_id}']['type'] == 'MOVIE':
                    self.movie_subtitle(data, program_id)
                else:
                    self.series_subtitle(data, program_id)
        else:
            self.logger.error(res.text)
