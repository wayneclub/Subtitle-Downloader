#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from KKTV
"""

import logging
import os
import re
import shutil
import orjson
from common.utils import get_locale, Platform, http_request, HTTPMethod, check_url_exist, download_file_multithread
from common.subtitle import convert_subtitle
from services.service import Service


class KKTV(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.api = {
            'play': 'https://www.kktv.me/play/{drama_id}010001'
        }

    def download_subtitle(self):

        drama_id = os.path.basename(self.url)

        play_url = self.api['play'].format(drama_id=drama_id)

        response = http_request(session=self.session,
                                url=play_url, method=HTTPMethod.GET, raw=True)

        match = re.search(r'({\"props\":{.*})', response)
        data = orjson.loads(match.group(1))

        if drama_id in data['props']['initialState']['titles']['byId']:
            drama = data['props']['initialState']['titles']['byId'][drama_id]
        else:
            self.logger.error(self._("\nSeries not found!"))
            exit(0)

        if drama:
            if 'title' in drama:
                title = drama['title']

            if 'titleType' in drama and drama['titleType'] == 'film':
                film = True
            else:
                film = False

            anime = False
            if 'genres' in drama:
                for genre in drama['genres']:
                    if 'title' in genre and genre['title'] == '動漫':
                        anime = True

            if 'totalSeriesCount' in drama:
                season_num = drama['totalSeriesCount']

            if film or anime:
                self.logger.info("\n%s", title)
            else:
                if 'dual_subtitle' in drama['contentLabels']:
                    self.logger.info(self._("\n%s total: %s season(s) (Provide bilingual subtitles)"),
                                     title, season_num)
                else:
                    self.logger.info(
                        self._("\n%s total: %s season(s)"), title, season_num)

            if 'series' in drama:
                for season in drama['series']:
                    season_index = int(season['title'][1])
                    if not self.download_season or season_index == self.download_season:
                        season_name = str(season_index).zfill(2)
                        episode_num = len(season['episodes'])

                        folder_path = os.path.join(self.output, title)

                        if film:
                            self.logger.info(self._(
                                "\nDownload:\n---------------------------------------------------------------"))
                        elif self.last_episode:
                            self.logger.info(
                                self._(
                                    "\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                season_index,
                                episode_num,
                                season_index)

                            season['episodes'] = [list(season['episodes'])[-1]]
                            folder_path = f'{folder_path}.S{season_name}'
                        elif anime:
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

                        ja_lang = False
                        ko_lang = False
                        subtitle_zh_urls = []
                        subtitle_zh_names = []
                        subtitle_ja_urls = []
                        subtitle_ja_names = []
                        subtitle_ko_urls = []
                        subtitle_ko_names = []
                        for episode in season['episodes']:
                            episode_index = int(
                                episode['id'].replace(episode['seriesId'], ''))
                            if len(season['episodes']) < 100:
                                episode_name = str(episode_index).zfill(2)
                            else:
                                episode_name = str(episode_index).zfill(3)

                            if not episode['subtitles']:
                                self.logger.info(
                                    self._("\nSorry, there's no embeded subtitles in this video!"))
                                exit(0)

                            if 'ja' in episode['subtitles']:
                                ja_lang = True
                            if 'ko' in episode['subtitles']:
                                ko_lang = True

                            episode_uri = episode['mezzanines']['dash']['uri']
                            if episode_uri:
                                episode_link_search = re.search(
                                    r'https:\/\/theater\.kktv\.com\.tw([^"]+)_dash\.mpd', episode_uri)
                                if episode_link_search:
                                    episode_link = episode_link_search.group(
                                        1)
                                    epsiode_search = re.search(
                                        drama_id + '[0-9]{2}([0-9]{4})_', episode_uri)
                                    if epsiode_search:
                                        subtitle_link = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/zh-Hant.vtt'

                                        ja_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ja.vtt')

                                        ko_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ko.vtt')

                                        if film:
                                            file_name = f'{title}.WEB-DL.{Platform.KKTV}.zh-Hant.vtt'
                                        elif anime:
                                            file_name = f'{title}E{episode_name}.WEB-DL.{Platform.KKTV}.zh-Hant.vtt'
                                        else:
                                            file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.{Platform.KKTV}.zh-Hant.vtt'
                                            ja_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ja.vtt')
                                            ko_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ko.vtt')

                                            ja_folder_path = os.path.join(
                                                folder_path, 'ja')
                                            ko_folder_path = os.path.join(
                                                folder_path, 'ko')

                                        os.makedirs(
                                            folder_path, exist_ok=True)

                                        subtitle_zh_urls.append(subtitle_link)
                                        subtitle_zh_names.append(file_name)

                                        if ja_lang and check_url_exist(ja_subtitle_link):
                                            os.makedirs(
                                                ja_folder_path, exist_ok=True)
                                            subtitle_ja_urls.append(
                                                ja_subtitle_link)
                                            subtitle_ja_names.append(
                                                ja_file_name)

                                        if ko_lang and check_url_exist(ko_subtitle_link):
                                            os.makedirs(
                                                ko_folder_path, exist_ok=True)
                                            subtitle_ko_urls.append(
                                                ko_subtitle_link)
                                            subtitle_ko_names.append(
                                                ko_file_name)

                        download_file_multithread(
                            subtitle_zh_urls, subtitle_zh_names, folder_path)

                        if ja_folder_path and ja_lang:
                            download_file_multithread(
                                subtitle_ja_urls, subtitle_ja_names, ja_folder_path)
                            convert_subtitle(
                                folder_path=ja_folder_path, lang=self.locale)
                        if ko_folder_path and ko_lang:
                            download_file_multithread(
                                subtitle_ko_urls, subtitle_ko_names, ko_folder_path)
                            convert_subtitle(
                                folder_path=ko_folder_path, lang=self.locale)

                        convert_subtitle(
                            folder_path=folder_path, ott=Platform.KKTV, lang=self.locale)

    def main(self):
        self.download_subtitle()
