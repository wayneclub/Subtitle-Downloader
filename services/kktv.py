#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from KKTV
"""
from __future__ import annotations
import os
import re
import shutil
import sys
import orjson
from utils.io import rename_filename, download_files
from utils.helper import get_locale, check_url_exist
from utils.subtitle import convert_subtitle
from services.service import Service


class KKTV(Service):
    """
    Service code for the KKTV streaming service (https://www.kktv.me/).

    Authorization: None
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.title_id = os.path.basename(args.url)

    def movie_metadata(self, data):
        title = data['title'].strip()
        release_year = data['releaseYear']

        self.logger.info("\n%s (%s)", title, release_year)

        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)
        episode_id = data['series'][0]['episodes'][0]['id']
        file_name = f'{title}.WEB-DL.{self.platform}.zh-Hant.vtt'

        self.logger.warning(
            self._("\nSorry, there's no embedded subtitles in this video!"))
        sys.exit(0)

    def series_metadata(self, data):

        season_index = re.search(r'(.+)S(\d+)', data['title'])
        if season_index:
            title = season_index.group(1).strip()
            season_index = int(season_index.group(2))
        else:
            title = data['title'].strip()

        if 'totalSeriesCount' in data:
            season_num = data['totalSeriesCount']

        self.logger.info(self._("\n%s total: %s season(s)"), title, season_num)

        if 'series' in data:
            for season in data['series']:
                if not season_index:
                    season_index = int(re.findall(
                        r'第(.+)季', season['title'])[0].strip())
                if not self.download_season or season_index in self.download_season:
                    episode_num = len(season['episodes'])
                    name = rename_filename(
                        f'{title}.S{str(season_index).zfill(2)}')
                    folder_path = os.path.join(self.download_path, name)

                    if self.last_episode:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                         season_index,
                                         episode_num,
                                         season_index)

                        season['episodes'] = [list(season['episodes'])[-1]]
                    else:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index,
                                         episode_num)

                    last_ep = [ep['title'] for ep in season['episodes']
                               if re.search(r'第(\d+)[集|話]', ep['title'])][-1]
                    last_ep = re.findall(r'第(\d+)[集|話]', last_ep)

                    if last_ep:
                        fill_num = len(str(last_ep[0]))
                        if fill_num < 2:
                            fill_num = 2

                    languages = set()
                    subtitles = []
                    ja_lang = False
                    ko_lang = False
                    for episode in season['episodes']:
                        episode_index = re.findall(
                            r'第(\d+)[集|話]', episode['title'])
                        if episode_index:
                            episode_index = int(episode_index[0])
                        else:
                            episode_index = int(
                                episode['id'].replace(episode['seriesId'], ''))

                        if not self.download_episode or episode_index in self.download_episode:
                            file_name = f"{name}E{str(episode_index).zfill(fill_num)}.WEB-DL.{self.platform}.zh-Hant.vtt"

                            if not episode['subtitles']:
                                self.logger.error(
                                    self._("\nSorry, there's no embedded subtitles in this video!"))
                                break

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
                                        self.title_id + '[0-9]{2}([0-9]{4})_', episode_uri)
                                    if epsiode_search:
                                        subtitle_link = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/zh-Hant.vtt'

                                        ja_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ja.vtt')

                                        ko_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ko.vtt')

                                        ja_file_name = file_name.replace(
                                            'zh-Hant.vtt', 'ja.vtt')
                                        ko_file_name = file_name.replace(
                                            'zh-Hant.vtt', 'ko.vtt')

                                        ja_folder_path = os.path.join(
                                            folder_path, 'ja')
                                        ko_folder_path = os.path.join(
                                            folder_path, 'ko')

                                        if check_url_exist(subtitle_link):
                                            os.makedirs(
                                                folder_path, exist_ok=True)

                                            languages.add(folder_path)

                                            subtitle = dict()
                                            subtitle['name'] = file_name
                                            subtitle['path'] = folder_path
                                            subtitle['url'] = subtitle_link
                                            subtitles.append(subtitle)

                                        if ja_lang and check_url_exist(ja_subtitle_link):
                                            os.makedirs(
                                                ja_folder_path, exist_ok=True)
                                            languages.add(ja_folder_path)
                                            subtitle = dict()
                                            subtitle['name'] = ja_file_name
                                            subtitle['path'] = ja_folder_path
                                            subtitle['url'] = ja_subtitle_link
                                            subtitles.append(subtitle)

                                        if ko_lang and check_url_exist(ko_subtitle_link):
                                            os.makedirs(
                                                ko_folder_path, exist_ok=True)
                                            languages.add(ko_folder_path)
                                            subtitle = dict()
                                            subtitle['name'] = ko_file_name
                                            subtitle['path'] = ko_folder_path
                                            subtitle['url'] = ko_subtitle_link
                                            subtitles.append(subtitle)

                    self.download_subtitle(
                        subtitles=subtitles, languages=languages, folder_path=folder_path)

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, lang=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, lang=self.locale)

    def main(self):
        play_url = self.config['api']['play'].format(title_id=self.title_id)

        res = self.session.get(url=play_url, timeout=5)
        if res.ok:
            match = re.search(r'({\"props\":{.*})', res.text)
            data = orjson.loads(match.group(1))

            if self.title_id in data['props']['initialState']['titles']['byId']:
                data = data['props']['initialState']['titles']['byId'][self.title_id]
            else:
                self.logger.error(self._("\nSeries not found!"))
                sys.exit(0)

            if 'titleType' in data and data['titleType'] == 'film':
                self.movie_metadata(data)
            else:
                self.series_metadata(data)
        else:
            self.logger.error(res.text)
