#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from MyVideo
"""

import base64
import os
import re
import sys
import time
from bs4 import BeautifulSoup
from cn2an import cn2an
import orjson
from utils.io import rename_filename, download_files
from utils.helper import get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.service import Service


class MyVideo(Service):
    """
    Service code for MyVideo streaming service (https://www.myvideo.net.tw/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def movie_metadata(self, data):
        title = data['name'].strip()
        release_year = data['release_year']
        self.logger.info("\n%s (%s)", title, release_year)
        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)

        filename = f"{title}.WEB-DL.{self.platform}.zh-Hant.vtt"
        movie_id = os.path.basename(data['url'])
        media_info = self.get_media_info(
            content_id=movie_id, filename=filename)

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

    def series_metadata(self, data, season_list):
        """Get series metadata"""

        title = data['name'].strip()
        self.logger.info(self._("\n%s total: %s season(s)"),
                         title, len(season_list))

        for season in season_list:
            season_index = season['index']
            if not self.download_season or season_index in self.download_season:
                episode_list = []
                res = self.session.get(season['url'], timeout=5)
                if res.ok:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for episode in soup.find_all('span', class_='episodeIntro'):
                        episode = episode.find('a')
                        episode_search = re.search(r'第(\d+)集', episode.text)
                        if episode_search and not '預告' in episode.text:
                            episode_list.append({
                                'index': int(episode_search.group(1)),
                                'id': os.path.basename(episode['href']),
                            })

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
                    episode_index = episode['index']
                    if not self.download_episode or episode_index in self.download_episode:
                        filename = f"{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.zh-Hant.vtt"
                        media_info = self.get_media_info(
                            content_id=episode['id'], filename=filename)
                        subs, lang_paths = self.get_subtitle(
                            media_info=media_info, folder_path=folder_path, filename=filename)

                        if not subs:
                            break

                        subtitles += subs
                        languages = set.union(languages, lang_paths)

                self.download_subtitle(
                    subtitles=subtitles, languages=languages, folder_path=folder_path)

    def check_session(self):
        res = self.session.get(url=self.config['api']['check_session'].format(
            time=int(time.time() * 1000)), timeout=5)
        if res.ok:
            if res.json().get('msg') == 'success':
                return True
            else:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_media_info(self, content_id, filename):

        media_info_url = self.config['api']['media_info'].format(
            content_id=content_id)

        res = self.session.get(url=media_info_url, timeout=5)
        self.check_session()

        if res.ok:
            data = res.json()
            if data.get('data'):
                data = orjson.loads(base64.b64decode(data['data']))
                self.logger.debug("media_info: %s", data)
                return data
            elif data.get('error'):
                self.logger.error("%s\nError: %s\n", os.path.basename(
                    filename), orjson.loads(data['error'])['errorMessage'])
            else:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_subtitle(self, media_info, folder_path, filename):

        lang_paths = set()
        subtitles = []
        if media_info:
            if 'subtitleList' in media_info:
                for sub in media_info['subtitleList']:
                    sub_lang = get_language_code(sub['languageCode'])

                    if len(lang_paths) > 1:
                        lang_folder_path = os.path.join(folder_path, sub_lang)
                    else:
                        lang_folder_path = folder_path
                    lang_paths.add(lang_folder_path)

                    os.makedirs(lang_folder_path,
                                exist_ok=True)

                    subtitles.append({
                        'name': filename,
                        'path': folder_path,
                        'url': sub['subtitleUrl']
                    })
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

    def main(self):
        """Download subtitle from MyVideo"""

        res = self.session.get(self.url, timeout=5)
        if res.ok:
            soup = BeautifulSoup(res.text, 'html.parser')
            data = ''
            release_year = ''
            for meta in soup.find_all('li', class_='introList'):
                if meta.text.isdigit() and len(meta.text) == 4:
                    release_year = meta.text
                    break

            for meta in soup.find_all('script', type='application/ld+json'):
                if 'VideoObject' not in meta.text:
                    data = orjson.loads(meta.text)
                    data['release_year'] = release_year
                    break

            if data:
                if '/details/0/' in self.url or 'seriesType=0' in self.url:
                    self.movie_metadata(data)
                else:
                    season_list = []
                    for season in soup.find('ul', class_='seasonSelectorList').find_all('a'):
                        season_search = re.search(r'第(.+?)季', season.text)
                        if season_search and not '國語版' in season.text:
                            season_list.append({
                                'index': int(cn2an(season_search.group(1))),
                                'url': f"https://www.myvideo.net.tw/{season['href']}",
                            })
                    if not season_list:
                        season_list.append({
                            'index': 1,
                            'url': self.url,
                        })

                    self.series_metadata(data, season_list)
