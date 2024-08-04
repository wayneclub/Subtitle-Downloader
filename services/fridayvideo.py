#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Friday Video
"""

import os
from pathlib import Path
import re
import sys
import time
from configs.config import config, credentials, user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.baseservice import BaseService


class FridayVideo(BaseService):
    """
    Service code for Friday Video streaming service (https://video.friday.tw).

    Authorization: Cookies

    GEOFENCE: tw
    """

    GEOFENCE = ['tw']

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)
        self.monitor_url = ''

    def get_content_type(self, content_type) -> int:
        """Get media content type"""
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

        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)

        media_info = {
            'streaming_id': data['streamingId'],
            'streaming_type': data['streamingType'],
            'content_type':  data['contentType'],
            'content_id':  data['contentId'],
            'subtitle': False
        }

        filename = f"{title}.WEB-DL.{self.platform}.vtt"

        languages = set()
        subtitles = []
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

    def filter_episode_list(self, data) -> tuple[list, list]:
        """Restrcut episode list"""

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

            filename = f"{title}.S{str(season_index).zfill(2)}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt"

            episode['season_index'] = season_index
            episode['episode_index'] = episode_index
            episode['filename'] = filename
            episode_list.append(episode)

        self.logger.debug("episode_list: %s", episode_list)

        return season_list, episode_list

    def series_metadata(self, data):

        title = re.sub(r'(.+?)(第.+[季|彈])*', '\\1', data['chineseName']).strip()
        original_title = data['englishName'].replace('，', ',')

        episode_list_url = self.config['api']['episode_list'].format(
            content_id=data['contentId'], content_type=data['contentType'])
        self.logger.debug(episode_list_url)

        res = self.session.get(url=episode_list_url, timeout=5)

        if res.ok:
            data = res.json()['data']
            season_list, episode_list = self.filter_episode_list(data)
            self.logger.debug(
                "season list: %s\nepisode list: %s", season_list, episode_list)
            season_num = len(set(season_list))
            episode_num = len(episode_list)

            if season_num > 1:
                self.logger.info(
                    self._("\n%s (%s) total: %s season(s)"), title, original_title, season_num)
            else:
                self.logger.info("\n%s (%s)", title, original_title)

            if self.last_episode:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                 season_list[-1],
                                 season_list.count(season_list[-1]),
                                 season_list[-1])
                episode_list = [episode_list[-1]]
            else:
                if self.download_season:
                    episode_count = []
                    for season in self.download_season:
                        episode_count.append(season_list.count(season))
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                     self.download_season,
                                     episode_count)
                else:
                    if season_num > 1:
                        self.logger.info(self._("\nTotal: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         episode_num)
                    else:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_num,
                                         episode_num)

            languages = set()
            subtitles = []

            for episode in episode_list:
                if not self.download_season or episode['season_index'] in self.download_season:
                    if not self.download_episode or episode['episode_index'] in self.download_episode:
                        filename = episode['filename']
                        folder_path = os.path.join(
                            self.download_path, rename_filename(filename.split('E')[0]))
                        media_info = {
                            'streaming_id': episode['streamingId'],
                            'streaming_type': episode['streamingType'],
                            'content_type':  episode['contentType'],
                            'content_id':  episode['contentId'],
                            'subtitle':  'false'
                        }

                        subs, lang_paths = self.get_subtitle(
                            media_info=media_info, folder_path=folder_path, filename=filename)
                        subtitles += subs
                        languages = set.union(languages, lang_paths)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

        else:
            sys.exit(1)

    def get_media_info(self, media_info, filename) -> dict:
        """Get mediainfo"""

        client_id = self.cookies['uid']
        media_info_url = self.config['api']['media_info'].format(streaming_id=media_info['streaming_id'],
                                                                 streaming_type=media_info['streaming_type'],
                                                                 content_type=media_info['content_type'],
                                                                 content_id=media_info['content_id'],
                                                                 subtitle=media_info['subtitle'],
                                                                 client_id=client_id,
                                                                 time_stamp=int(time.time())*1000)

        res = self.session.get(url=media_info_url, timeout=5)
        # self.fet_monitor(self.monitor_url)

        if res.ok:
            if 'redirectUri' in res.text:
                self.logger.debug(res.text)
                self.logger.error(
                    self._("\nLogin access token is expired!\nPlease clear browser cookies and re-download cookies!"))
                os.remove(
                    Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
                sys.exit(1)
            else:
                data = res.json()
                if 'data' in data:
                    data = data['data']
                    self.logger.debug("media_info: %s", data)
                    return data
                else:
                    self.logger.error("%s\nError: %s\n", os.path.basename(
                        filename), data['message'])
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def fet_monitor(self, url):
        """Check api call from friday website"""

        data = f'${int(time.time())*1000}'

        res = self.session.post(
            url=self.config['api']['fet_monitor'].format(url=url), data=data)
        if res.ok:
            if res.text == 'OK(Webserver)':
                return True
            else:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_subtitle(self, media_info, folder_path, filename):
        data = self.get_media_info(media_info, filename)

        lang_paths = set()
        subtitles = []

        if data and 'subtitleList' in data and data['subtitleList']:
            for sub in data['subtitleList']:
                sub_lang = get_language_code(
                    os.path.splitext(os.path.basename(sub['url']))[0].split('.')[-1])
                if sub_lang == 'de':
                    sub_lang = 'mul'

                if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                os.makedirs(lang_folder_path,
                            exist_ok=True)

                subtitles.append({
                    'name': filename.replace('.vtt', f'.{sub_lang}.vtt'),
                    'path': lang_folder_path,
                    'url': sub['url'].replace('http:', 'https:')
                })

        return subtitles, lang_paths

    def download_subtitle(self, subtitles, folder_path, languages=None):
        if subtitles:
            headers = {'user-agent': user_agent,
                       'referer': 'https://video.friday.tw/'}
            download_files(subtitles, headers)
            if languages:
                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
        """Download subtitle from friDay"""
        self.cookies['JSESSIONID'] = ''
        self.cookies['login_accessToken'] = ''
        self.session.cookies.update(self.cookies)

        content_search = re.search(
            r'(https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/(\d+))', self.url)

        if content_search:
            self.monitor_url = content_search.group(1)
            content_id = content_search.group(3)
            content_type = self.get_content_type(content_search.group(2))
        else:
            self.logger.error("\nCan't detect content id: %s", self.url)
            sys.exit(1)

        title_url = self.config['api']['title'].format(
            content_id=content_id, content_type=content_type)
        res = self.session.post(title_url, timeout=5)
        # self.fet_monitor(self.monitor_url)

        if res.ok:
            if '/pkmslogout' in res.text:
                self.logger.info(
                    "\nCookies is expired!\nPlease log out (https://video.friday.tw/logout), login, and re-download cookies!")
                os.remove(
                    Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
                sys.exit(1)
            else:
                data = res.json()
                if data.get('data'):
                    data = data['data']['content']
                else:
                    self.logger.error(data['message'])
                    sys.exit(1)

                if content_type == 1:
                    self.movie_metadata(data)
                else:
                    self.series_metadata(data)
        else:
            self.logger.error(res.text)
