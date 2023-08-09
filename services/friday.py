#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Friday影音
"""

import logging
import os
import re
import shutil
import sys
import time
from configs.config import Platform
from utils.cookies import Cookies
from utils.helper import get_locale, download_files
from utils.subtitle import convert_subtitle
from services.service import Service


class Friday(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.credential = self.config.credential(Platform.FRIDAY)
        self.cookies = Cookies(self.credential)

        self.api = {
            'title': 'https://video.friday.tw/api2/content/get?contentId={content_id}&contentType={content_type}&srcRecommendId=-1&recommendId=-1&eventPageId=&offset=0&length=1',
            'episode_list': 'https://video.friday.tw/api2/episode/list?contentId={content_id}&contentType={content_type}&offset=0&length=40&mode=2',
            'media_info': 'https://video.friday.tw/api2/streaming/get?streamingId={streaming_id}&streamingType={streaming_type}&contentType={content_type}&contentId={content_id}&clientId={client_id}&haveSubtitle={subtitle}&isEst=false&_={time_stamp}',
        }

    def get_content_type(self, content_type):
        program = {
            'movie': 1,
            'drama': 2,
            'anime': 3,
            'show': 4
        }

        if program.get(content_type):
            return program.get(content_type)

    def movie_metadata(self, data):
        title = data['chineseName'].strip()
        original_title = data['englishName'].replace('，', ',')
        release_year = data['year']

        self.logger.info("\n%s (%s) [%s]", title, original_title, release_year)

        title = f'{title}.{release_year}'

        folder_path = os.path.join(
            self.download_path, self.ripprocess.rename_file_name(title))

        media_info = {
            'streaming_id': data['streamingId'],
            'streaming_type': data['streamingType'],
            'content_type':  data['contentType'],
            'content_id':  data['contentId'],
            'subtitle': False
        }

        file_name = f"{title}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt"

        languages = set()
        subtitles = []
        subs, lang_paths = self.get_subtitle(media_info=media_info, folder_path=folder_path, file_name=file_name)
        subtitles += subs
        languages = set.union(languages, lang_paths)

        if subtitles:
            self.logger.info(
            self._(
                "\nDownload: %s\n---------------------------------------------------------------"),
            file_name)

        self.download_subtitle(
                        subtitles=subtitles, languages=languages, folder_path=folder_path)


    def filter_episode_list(self, data):
        episode_list = []
        season_list = []
        for episode in data['episodeList']:
            if '搶先看' in episode['episodeName'] or '預告' in episode['episodeName']:
                continue

            season_search = re.search(
                r'(.+)第(\d+)季', episode['chineseName'])

            if season_search:
                title = season_search.group(1).strip()
                season_index = int(season_search.group(2))
            else:
                title = episode['chineseName'].replace(
                    episode['episodeName'], '')
                season_index = 1

            if re.search(r"^[a-zA-Z\d :\.0-9']+$", episode['englishName']):
                title = episode['englishName'].replace(
                    episode['episodeName'], '')

            season_list.append(season_index)

            if '季' in episode['episodeName']:
                episode_index = int(episode['episodeName'].split('季')[-1])
            elif episode['episodeName'].isdecimal():
                episode_index = int(episode['episodeName'])
            else:
                if episode['episodeName'][-1].isdecimal():
                    if not title in episode['episodeName']:
                        title = episode['episodeName'][:-2]
                        season_index = 1
                        episode_index = int(episode['episodeName'][-1])
                    else:
                        season_index = 0
                        episode_index = int(episode['episodeName'][-1])
                else:
                    season_index = 0
                    episode_index = 1

            file_name = f"{title}.S{str(season_index).zfill(2)}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt"

            episode['season_index'] = season_index
            episode['episode_index'] = episode_index
            episode['file_name'] = file_name
            episode_list.append(episode)

        self.logger.debug("episode_list: %s", episode_list)

        return season_list, episode_list

    def series_metadata(self, data):
        """Download subtitle from friDay"""

        title = re.sub(r'(.+?)(第.+[季|彈])*', '\\1', data['chineseName']).strip()
        original_title = data['englishName'].replace('，', ',')

        episode_list_url = self.api['episode_list'].format(
            content_id=data['contentId'], content_type=data['contentType'])
        self.logger.debug(episode_list_url)

        res = self.session.get(url=episode_list_url)

        if res.ok:
            data = res.json()['data']
            season_list, episode_list = self.filter_episode_list(data)
            self.logger.debug(
                "season list: %s\nepisode list: %s", season_list, episode_list)
            season_num = len(set(season_list))
            episode_num = len(episode_list)

            if season_num > 1:
                self.logger.info(
                    "\n%s (%s) total: %s season(s)", title, original_title, season_num)
            else:
                self.logger.info("\n%s (%s)", title, original_title)

            if self.last_episode:
                self.logger.info("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------",
                                 season_list[-1],
                                 season_list.count(season_list[-1]),
                                 season_list[-1])
                episode_list = [episode_list[-1]]
            else:
                if self.download_season:
                    episode_count = []
                    for season in self.download_season:
                        episode_count.append(season_list.count(season))
                    self.logger.info("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------",
                                     self.download_season,
                                     episode_count)
                else:
                    if season_num > 1:
                        self.logger.info("\nTotal: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------",
                                         episode_num)
                    else:
                        self.logger.info("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------",
                                         season_num,
                                         episode_num)

            languages = set()
            subtitles = []

            for episode in episode_list:
                if not self.download_season or episode['season_index'] in self.download_season:
                    if not self.download_episode or episode['episode_index'] in self.download_episode:
                        file_name = episode['file_name']
                        folder_path = os.path.join(
                            self.download_path, self.ripprocess.rename_file_name(file_name.split('E')[0]))
                        media_info = {
                            'streaming_id': episode['streamingId'],
                            'streaming_type': episode['streamingType'],
                            'content_type':  episode['contentType'],
                            'content_id':  episode['contentId'],
                            'subtitle':  'false'
                        }

                        subs, lang_paths = self.get_subtitle(media_info=media_info, folder_path=folder_path, file_name=file_name)
                        subtitles += subs
                        languages = set.union(languages, lang_paths)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_media_info(self, media_info):
        cookies = self.cookies.get_cookies()

        client_id = cookies['uid']
        client_device_id = cookies['udid']
        x_friday = cookies['x_friday']
        fet_token = cookies['fetToken']
        login_access_token = cookies['login_accessToken']
        id_token = cookies['idToken']

        headers = {
            'user-agent': self.user_agent,
            'Cookie': f'udid={client_device_id};x_friday={x_friday};logined=true;uid={client_id};login_accessToken={login_access_token};idToken={id_token};fetToken={fet_token};'
        }

        media_info_url = self.api['media_info'].format(streaming_id=media_info['streaming_id'],
                                                       streaming_type=media_info['streaming_type'],
                                                       content_type=media_info['content_type'],
                                                       content_id=media_info['content_id'],
                                                       subtitle=media_info['subtitle'],
                                                       client_id=client_id,
                                                       time_stamp=int(time.time())*1000)

        res = self.session.get(
            url=media_info_url, headers=headers)
        if res.ok:
            if 'redirectUri' in res.text:
                self.logger.debug(res.text)
                self.logger.info(
                    "\nLogin access token (%s) is expired!\nPlease log out (https://video.friday.tw/logout), login, and re-download cookies", login_access_token)
                os.remove(self.credential['cookies_file'])
                sys.exit()
            else:
                data = res.json()
                if 'data' in data:
                    data = data['data']
                    self.logger.debug("media_info: %s", data)
                    return data
                else:
                    self.logger.error("Error: %s", data['message'])
        else:
            self.logger.error(res.text)
            sys.exit(1)



    def get_subtitle(self, media_info, folder_path, file_name):
        data = self.get_media_info(media_info)

        lang_paths = set()
        subtitles = []

        if data and 'subtitleList' in data and data['subtitleList']:

            for sub in data['subtitleList']:
                sub_lang = self.config.get_language_code(
                os.path.splitext(os.path.basename(sub['url']))[0].split('.')[-1])
                if sub_lang == 'deu':
                    sub_lang = 'mul'

                if len(lang_paths) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                os.makedirs(lang_folder_path,
                            exist_ok=True)

                subtitles.append({
                    'name': file_name,
                    'path': folder_path,
                    'url': sub['url'].replace('http:', 'https:')
                })

        else:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            sys.exit(0)

        return subtitles, lang_paths


    def download_subtitle(self, subtitles, folder_path, languages=None):
        if subtitles:
            download_files(subtitles)
            if languages:
                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, lang=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.FRIDAY, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)

    def main(self):
        """Download subtitle from friDay"""

        self.cookies.load_cookies('uid')

        content_search = re.search(
            r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/(\d+)', self.url)

        if content_search:
            content_id = content_search.group(2)
            content_type = self.get_content_type(content_search.group(1))
        else:
            self.logger.error("\nCan't detect content id: %s", self.url)
            sys.exit(-1)

        res = self.session.post(self.api['title'].format(
            content_id=content_id, content_type=content_type))
        if res.ok:
            data = res.json()
            if data.get('data'):
                data = data['data']['content']
            else:
                self.logger.error(data['message'])
                sys.exit(-1)

            if content_type == 1:
                self.movie_metadata(data)
            else:
                self.series_metadata(data)
        else:
            self.logger.error(res.text)
