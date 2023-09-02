#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Catch Play
"""
import os
from pathlib import Path
import re
import shutil
import sys
import orjson
from configs.config import user_agent, config, credentials
from utils.io import rename_filename, download_files
from utils.helper import get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.service import Service


class CatchPlay(Service):
    """
    Service code for CatchPlay streaming service (https://www.catchplay.com).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)
        self.access_token = self.get_access_token()

    def get_access_token(self):

        res = self.session.get(url=self.config['api']['auth'], timeout=5)
        if res.ok:
            if '</html>' in res.text:
                self.logger.error(
                    self._("\nOut of services! Please use proxy to bypass."))
                sys.exit(1)
            data = res.json()
            self.logger.debug("User: %s", data)
            return data['access_token']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def movie_subtitle(self, data, program_id):
        title = data['apolloState'][f'Program:{program_id}']['title']['local']
        english_title = data['apolloState'][f'Program:{program_id}']['title']['eng']
        release_year = data['apolloState'][f'Program:{program_id}']['releaseYear']
        self.logger.info("\n%s (%s) [%s]", title, english_title, release_year)

        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{self.platform}.vtt'

        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

        vcms_access_token = self.get_vcms_access_token(program_id)
        if vcms_access_token:
            self.get_subtitle(
                vcms_access_token['play_video_id'], vcms_access_token['play_token'], folder_path, file_name)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def series_subtitle(self, data, program_id):
        main_program = 'getMainProgram({\"id\":\"' + program_id + '\"})'
        main_id = data['apolloState']['ROOT_QUERY'][main_program]['__ref']
        title = data['apolloState'][main_id]['title']['local']
        english_title = data['apolloState'][main_id]['title']['eng']
        season_num = data['apolloState'][main_id]['totalChildren']

        self.logger.info(self._("\n%s (%s) total: %s season(s)"),
                         title, english_title, season_num)

        for season in data['apolloState'][main_id]['children']:
            season_id = season['__ref']
            season_index = int(
                data['apolloState'][season_id]['title']['short'].replace('S', ''))

            if not self.download_season or season_index in self.download_season:
                name = rename_filename(
                    f'{title}.S{str(season_index).zfill(2)}')
                folder_path = os.path.join(self.download_path, name)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                episode_list = data['apolloState'][season_id]['children']
                episode_num = len(episode_list)
                if self.last_episode:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num,
                                     season_index)
                    episode_list = [episode_list[-1]]
                elif self.download_episode:
                    self.logger.info(
                        self._("\nSeason %s total: %s episode(s)\tdownload episode: %s\n---------------------------------------------------------------"), season_index, episode_num, self.download_episode)
                else:
                    self.logger.info(
                        self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                for episode_index, episode in enumerate(episode_list, start=1):
                    if not self.download_episode or episode_index in self.download_episode:
                        file_name = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'
                        episode_id = episode['__ref'].replace('Program:', '')
                        vcms_access_token = self.get_vcms_access_token(
                            episode_id)
                        if vcms_access_token:
                            self.logger.info(
                                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
                            self.get_subtitle(
                                vcms_access_token['play_video_id'], vcms_access_token['play_token'], folder_path, file_name)
                        else:
                            break

                convert_subtitle(folder_path=folder_path,
                                 platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def get_vcms_access_token(self, video_id):
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {self.access_token}',
            'user-agent': user_agent,
        }

        payload = {
            'force': False,
            'programType': 'Video',
            'videoId': video_id,
            'watchType': 'movie'
        }

        res = self.session.post(
            url=self.config['api']['play'], headers=headers, json=payload)
        if res.ok:
            data = res.json()
            self.logger.debug(data)
            return {
                'play_video_id': data['data']['catchplayVideoId'],
                'play_token': data['data']['playToken']
            }
        else:
            error_msg = res.json()['message']
            if 'No subscribe record' in error_msg:
                self.logger.error(
                    self._("\nPlease check your subscription plan, and make sure you are able to watch it online!"))
            elif 'Insufficient permission to access' in error_msg:
                self.logger.error(
                    self._("\nPlease renew the cookies!"))
                os.remove(
                    Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
            else:
                self.logger.error(
                    "Error: %s", error_msg)

            return None

    def get_subtitle(self, play_video_id, play_token, folder_path, file_name):
        headers = {
            'asiaplay-os-type': 'chrome',
            'asiaplay-device-model': 'mac os',
            'asiaplay-app-version': '3.0',
            'authorization': f'Bearer {play_token}',
            'user-agent': user_agent,
            'asiaplay-platform': 'desktop',
            'asiaplay-os-version': '97.0.4692',
            'asiaplay-device-type': 'web'
        }

        media_info_url = self.config['api']['media_info'].format(
            video_id=play_video_id)
        res = self.session.get(url=media_info_url, headers=headers)

        if res.ok:
            data = res.json()
            self.logger.debug('media_info: %s', data)
            if 'subtitleInfo' in data and data['subtitleInfo']:
                lang_paths = set()
                subtitles = []
                for sub in data['subtitleInfo']:
                    sub_lang = get_language_code(sub['language'])
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
        res = self.session.get(url=self.url, timeout=5)
        if res.ok:
            match = re.search(
                r'<script id=\"__NEXT_DATA__" type=\"application/json\">(.+?)<\/script>', res.text)
            if match:
                data = orjson.loads(match.group(1).strip())['props']
                program_id = os.path.basename(self.url)
                if data['apolloState'][f'Program:{program_id}']['type'] == 'MOVIE':
                    self.movie_subtitle(data, program_id)
                else:
                    self.series_subtitle(data, program_id)
        else:
            self.logger.error(res.text)
