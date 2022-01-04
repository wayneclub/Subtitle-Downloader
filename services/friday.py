#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Friday影音
"""

import logging
import os
import re
import shutil
import orjson
from bs4 import BeautifulSoup
from common.utils import get_locale, Platform, http_request, HTTPMethod, check_url_exist, download_file, download_files
from common.subtitle import convert_subtitle
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

    def download_subtitle(self):
        """Download subtitle from friDay"""

        content_search = re.search(
            r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/(.+)', self.url)
        content_type = self.get_content_type(content_search.group(1))
        content_id = content_search.group(2)

        response = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)

        web_content = BeautifulSoup(response, 'lxml')

        metadata = web_content.findAll(
            'script', attrs={'type': 'application/ld+json'})
        metadata = orjson.loads(str(metadata[1].string))

        title = re.sub(r'(.+?)(第.+[季|彈])*', '\\1', metadata['name']).strip()

        folder_path = os.path.join(self.output, title)

        if content_type > 1:
            episode_list_url = self.api['episode_list'].format(
                content_id=content_id, content_type=content_type)
            self.logger.debug(episode_list_url)

            data = http_request(session=self.session,
                                url=episode_list_url, method=HTTPMethod.GET)['data']

            episode_list = []
            season_list = []
            ja_lang = False
            dual_lang = False
            for episode in data['episodeList']:
                if '搶先看' in episode['episodeName']:
                    continue

                subtitle = dict()

                season_search = re.search(
                    r'第(\d+)季(\d+)', episode['chineseName'])

                if season_search:
                    season_index = int(season_search.group(1))
                else:
                    season_index = 1

                subtitle['season_index'] = season_index

                season_list.append(season_index)

                season_name = str(season_index).zfill(2)

                subtitle_link = self.api['sub'].format(
                    sid=episode['streamingId'])

                subtitle_link, ja_subtitle_link, dual_subtitle_link = self.get_subtitle_link(
                    subtitle_link)

                subtitle['zh'] = subtitle_link

                episode_name = episode['episodeName'].split('季')[-1]

                if episode_name.isdecimal():
                    file_name = f'{title}.S{season_name}E{episode_name.zfill(2)}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt'
                else:
                    file_name = f'{title}.{episode_name}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt'

                subtitle['name'] = file_name

                if ja_subtitle_link:
                    ja_lang = True
                    subtitle['ja'] = ja_subtitle_link
                if dual_subtitle_link:
                    dual_lang = True
                    subtitle['dual'] = dual_subtitle_link

                episode_list.append(subtitle)

            season_num = len(set(season_list))
            episode_num = len(episode_list)

            if season_num > 1:
                self.logger.info(
                    self._("\n%s total: %s season(s)"), title, season_num)
            else:
                self.logger.info("\n%s", title)

            if dual_lang:
                self.logger.info(self._("(Provide bilingual subtitles)"))
            elif ja_lang:
                self.logger.info(self._("(Provide Japanese subtitles)"))

            if self.last_episode:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                 season_index,
                                 season_list.count(season_index))
                episode_list = [episode_list[-1]]
                folder_path = f'{folder_path}.S{str(season_index).zfill(2)}'
            else:
                if self.download_season:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                     self.download_season,
                                     season_list.count(self.download_season))
                    folder_path = f'{folder_path}.S{str(self.download_season).zfill(2)}'
                else:
                    if season_num > 1:
                        self.logger.info(
                            self._(
                                "\nTotal: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                            episode_num)
                    else:
                        self.logger.info(
                            self._(
                                "\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                            season_index,
                            episode_num)
                        folder_path = f'{folder_path}.S{season_name}'

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            languages = set()
            subtitles = []
            for episode in episode_list:
                if not self.download_season or episode['season_index'] == self.download_season:
                    os.makedirs(folder_path, exist_ok=True)
                    languages.add(folder_path)
                    subtitle = dict()
                    subtitle['name'] = episode['name']
                    subtitle['path'] = folder_path
                    subtitle['url'] = episode['zh']
                    subtitles.append(subtitle)

                    if 'ja' in episode:
                        ja_folder_path = os.path.join(folder_path, 'ja')
                        os.makedirs(ja_folder_path, exist_ok=True)
                        ja_file_name = episode['name'].replace(
                            '.zh-Hant.vtt', '.ja.vtt')
                        languages.add(ja_folder_path)
                        subtitle = dict()
                        subtitle['name'] = ja_file_name
                        subtitle['path'] = ja_folder_path
                        subtitle['url'] = episode['ja']
                        subtitles.append(subtitle)

                    if 'dual' in episode:
                        dual_folder_path = os.path.join(folder_path, 'dual')
                        os.makedirs(dual_folder_path, exist_ok=True)
                        dual_file_name = episode['name'].replace(
                            '.zh-Hant.vtt', '.vtt')
                        languages.add(dual_folder_path)
                        subtitle = dict()
                        subtitle['name'] = dual_file_name
                        subtitle['path'] = dual_folder_path
                        subtitle['url'] = episode['dual']
                        subtitles.append(subtitle)

            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, lang=self.locale)
            convert_subtitle(folder_path=folder_path,
                             ott=Platform.FRIDAY, lang=self.locale)

        else:
            self.logger.info("\n%s", title)
            sid_search = web_content.find(
                'div', class_='popup-video-container content-vod')
            if sid_search:
                sub_search = re.search(
                    r'\/player\?sid=(.+?)&stype=.+', sid_search['data-src'])
                if sub_search:

                    subtitle_link = self.api['sub'].format(
                        sid=sub_search.group(1))
                    self.logger.debug(subtitle_link)

                    release_year = metadata['datePublished']
                    file_name = f"{title}.{release_year}.WEB-DL.{Platform.FRIDAY}.zh-Hant.vtt"
                    folder_path = f"{folder_path}.{release_year}"

                    if check_url_exist(subtitle_link):
                        self.logger.info(
                            self._(
                                "\nDownload: %s\n---------------------------------------------------------------"),
                            file_name)
                        os.makedirs(folder_path, exist_ok=True)
                        download_file(url=subtitle_link, output_path=os.path.join(
                            folder_path, file_name), lang=self.locale)
                        convert_subtitle(
                            folder_path=folder_path, ott=Platform.FRIDAY, lang=self.locale)
                    else:
                        self.logger.info(
                            self._("\nSorry, there's no embeded subtitles in this video!"))
                        exit(0)
                else:
                    self.logger.info(self._("\nThe film isn't released."))
                    exit(0)

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
                self._("\nSorry, there's no embeded subtitles in this video!"))
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

    def main(self):
        self.download_subtitle()
