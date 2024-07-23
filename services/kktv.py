#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from KKTV
"""
from __future__ import annotations
import os
import re
import sys
from utils.io import rename_filename, download_files
from utils.helper import get_locale
from utils.subtitle import convert_subtitle
from services.baseservice import BaseService


class KKTV(BaseService):
    """
    Service code for the KKTV streaming service (https://www.kktv.me/).

    Authorization: None
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.title_id = os.path.basename(args.url)

    def movie_metadata(self, data):
        title = data['title'].split('(')[0].strip()
        release_year = data['release_year']
        self.logger.info("\n%s (%s)", title, release_year)
        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)
        os.makedirs(folder_path, exist_ok=True)
        if 'series' in data:
            subtitles = []
            for media in data['series'][0]['episodes']:
                if not media['subtitles']:
                    self.logger.warning(
                        self._("\nSorry, there's no embedded subtitles in this video!"))
                    sys.exit(0)
                episode_link_search = re.search(
                    r'https:\/\/theater\.kktv\.com\.tw([^"]+)_dash\.mpd', media['mezzanines']['dash']['uri'])
                if episode_link_search:
                    episode_link = episode_link_search.group(
                        1)
                    if media['subtitles']:
                        for language in media['subtitles']:
                            subtitle = dict()
                            subtitle['name'] = f'{title}.WEB-DL.{self.platform}.{language}.vtt'
                            subtitle['path'] = folder_path
                            subtitle['url'] = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/{language}.vtt'
                            subtitles.append(subtitle)
            self.download_subtitle(
                subtitles=subtitles, languages=[folder_path], folder_path=folder_path)

    def series_metadata(self, data):
        title = data['title'].replace('(日)', '').replace('(中)', '').strip()
        title, season_index = self.get_title_and_season_index(title)

        self.logger.info(self._("\n%s total: %s season(s)"),
                         title, len(data['series']))
        if 'series' in data:
            for season in data['series']:
                if len(data['series']) > 1:
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

                    languages = set()
                    subtitles = []
                    for episode in season['episodes']:
                        episode_index = re.findall(
                            r'第(\d+)[集|話]', episode['title'])
                        if episode_index:
                            episode_index = int(episode_index[0])
                        else:
                            episode_index = int(
                                episode['id'].replace(episode['series_id'], ''))

                        if not self.download_episode or episode_index in self.download_episode:
                            if not episode['subtitles']:
                                self.logger.error(
                                    self._("\nSorry, there's no embedded subtitles in this video!"))
                                break

                            episode_link_search = re.search(
                                r'https:\/\/theater\.kktv\.com\.tw([^"]+)_dash\.mpd', episode['mezzanines']['dash']['uri'])
                            if episode_link_search:
                                episode_link = episode_link_search.group(
                                    1)
                                if episode['subtitles']:
                                    for language in episode['subtitles']:
                                        subtitle = dict()
                                        subtitle['name'] = f"{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.{language}.vtt"
                                        subtitle['path'] = os.path.join(folder_path, language) if len(
                                            episode['subtitles']) > 1 else folder_path
                                        os.makedirs(
                                            subtitle['path'], exist_ok=True)
                                        languages.add(subtitle['path'])
                                        subtitle[
                                            'url'] = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/{language}.vtt'
                                        subtitles.append(subtitle)

                    self.download_subtitle(
                        subtitles=subtitles, languages=languages, folder_path=folder_path)

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
        res = self.session.get(url=self.config["api"]["titles"].format(
            title_id=self.title_id), timeout=10)
        if res.ok:
            data = res.json()['data']
            if data.get('title_type') == 'film':
                self.movie = True
                self.movie_metadata(data)
            else:
                self.series_metadata(data)
        else:
            self.logger.error(res.text)
