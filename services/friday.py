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
from urllib.parse import parse_qs, urlparse
import orjson
from bs4 import BeautifulSoup
from configs.config import Platform
from utils.helper import get_locale, check_url_exist, download_files
from utils.subtitle import convert_subtitle
from services.service import Service


class Friday(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.api = {
            'episode_list': 'https://video.friday.tw/api2/episode/list?contentId={content_id}&contentType={content_type}&offset=0&length=40&mode=2',
            'sub': 'https://sub.video.friday.tw/{sid}.cht.vtt'
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

    def movie_metadata(self, data, media_info, original_title):

        title = data['name'].strip()
        release_year = data['datePublished']

        self.logger.info("\n%s (%s) [%s]", title, original_title, release_year)

        title = f'{title}.{release_year}'

        folder_path = os.path.join(
            self.download_path, self.ripprocess.rename_file_name(title))

        self.logger.info("\n%s", title)

        subtitle_link = self.api['sub'].format(
            sid=media_info['streaming_id'])
        self.logger.debug(subtitle_link)

        file_name = f"{title}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt"

        if check_url_exist(subtitle_link):
            self.logger.info(
                self._(
                    "\nDownload: %s\n---------------------------------------------------------------"),
                file_name)
            os.makedirs(folder_path, exist_ok=True)

            subtitles = []
            subtitle = dict()
            subtitle['name'] = file_name
            subtitle['path'] = folder_path
            subtitle['url'] = subtitle_link
            subtitles.append(subtitle)
            self.download_subtitle(subtitles=subtitles,
                                   folder_path=folder_path)

        else:
            self.logger.info(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            exit(0)

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

    def series_metadata(self, data, media_info, original_title):
        """Download subtitle from friDay"""

        title = re.sub(r'(.+?)(第.+[季|彈])*', '\\1', data['name']).strip()

        episode_list_url = self.api['episode_list'].format(
            content_id=media_info['content_id'], content_type=media_info['content_type'])
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

                        subtitle_link = self.api['sub'].format(
                            sid=episode['streamingId'])

                        subtitle_link, ja_subtitle_link, dual_subtitle_link = self.get_subtitle_link(
                            subtitle_link)

                        os.makedirs(folder_path, exist_ok=True)
                        languages.add(folder_path)
                        subtitle = dict()
                        subtitle['name'] = episode['file_name']
                        subtitle['path'] = folder_path
                        subtitle['url'] = subtitle_link
                        subtitles.append(subtitle)

                        if ja_subtitle_link:
                            ja_folder_path = os.path.join(
                                folder_path, 'ja')
                            os.makedirs(ja_folder_path, exist_ok=True)
                            ja_file_name = episode['file_name'].replace(
                                '.zh-Hant.vtt', '.ja.vtt')
                            languages.add(ja_folder_path)
                            subtitle = dict()
                            subtitle['name'] = ja_file_name
                            subtitle['path'] = ja_folder_path
                            subtitle['url'] = ja_subtitle_link
                            subtitles.append(subtitle)

                        if dual_subtitle_link:
                            dual_folder_path = os.path.join(
                                folder_path, 'dual')
                            os.makedirs(dual_folder_path, exist_ok=True)
                            dual_file_name = episode['file_name'].replace(
                                '.zh-Hant.vtt', '.mul.vtt')
                            languages.add(dual_folder_path)
                            subtitle = dict()
                            subtitle['name'] = dual_file_name
                            subtitle['path'] = dual_folder_path
                            subtitle['url'] = dual_subtitle_link
                            subtitles.append(subtitle)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_subtitle_link(self, subtitle_link):
        subtitle_link_2 = subtitle_link.replace(
            '.cht.vtt', '_80000000_ffffffff.cht.vtt')
        subtitle_link_3 = subtitle_link.replace(
            '.cht.vtt', '_ff000000_ffffffff.cht.vtt')

        ja_subtitle_link = ''
        dual_subtitle_link = ''
        if check_url_exist(subtitle_link):
            ja_subtitle_link = self.get_ja_subtitle_link(subtitle_link)
            dual_subtitle_link = self.get_dual_subtitle_link(subtitle_link)
        elif check_url_exist(subtitle_link_2):
            subtitle_link = subtitle_link_2
            ja_subtitle_link = self.get_ja_subtitle_link(subtitle_link)
            dual_subtitle_link = self.get_dual_subtitle_link(subtitle_link)
        elif check_url_exist(subtitle_link_3):
            subtitle_link = subtitle_link_3
            ja_subtitle_link = self.get_ja_subtitle_link(subtitle_link)
            dual_subtitle_link = self.get_dual_subtitle_link(subtitle_link)
        else:
            self.logger.info(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            exit(0)

        return subtitle_link, ja_subtitle_link, dual_subtitle_link

    def get_ja_subtitle_link(self, subtitle_link):
        ja_subtitle_link = subtitle_link.replace('.cht.vtt', '.jpn.vtt')
        if check_url_exist(ja_subtitle_link):
            return ja_subtitle_link

    def get_dual_subtitle_link(self, subtitle_link):
        dual_subtitle_link = subtitle_link.replace('.cht.vtt', '.deu.vtt')
        if check_url_exist(dual_subtitle_link):
            return dual_subtitle_link

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

        content_search = re.search(
            r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/(.+)', self.url)

        if not content_search:
            self.logger.error("\nCan't detect content id: %s", self.url)
            sys.exit(-1)

        content_type = self.get_content_type(content_search.group(1))
        content_id = content_search.group(2)

        res = self.session.get(url=self.url)

        if res.ok:
            original_title = re.findall(
                r'<h2 class=\"title-eng\">(.+)<\/h2>', res.text)[0].strip().replace('，', ',')

            web_content = BeautifulSoup(res.text, 'lxml')

            match = web_content.findAll(
                'script', attrs={'type': 'application/ld+json'})

            if match and len(match) > 1:
                data = orjson.loads(str(match[1].string))

                if content_type == 1:
                    play_url = re.findall(r'"(/player\?sid=.+")', res.text)
                    if play_url:
                        query = parse_qs(urlparse(play_url[0]).query)
                        media_info = {
                            'streaming_id': query['sid'][0],
                            'streaming_type': query['stype'][0],
                            'content_type':  query['ctype'][0],
                            'content_id':  query['cid'][0],
                            'subtitle':  query['subtitle'][0]
                        }
                    else:
                        self.logger.error("\nThe film hasn't released.")
                        sys.exit()

                    self.movie_metadata(data, media_info, original_title)
                else:
                    media_info = {
                        'content_type': content_type,
                        'content_id': content_id,
                    }
                    self.series_metadata(data, media_info, original_title)
