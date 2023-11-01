#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Crunchyroll
"""

import os
from pathlib import Path
import re
import shutil
import sys
from cn2an import cn2an
import yt_dlp
from services.baseservice import BaseService
from utils.helper import get_all_languages, get_language_code, get_locale
from utils.io import download_files, rename_filename
from utils.subtitle import convert_subtitle
from configs.config import config, credentials, user_agent


class Crunchyroll(BaseService):
    """
    Service code for Crunchyroll streaming service (https://www.crunchyroll.com/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)
        cookies = self.session.cookies.get_dict()
        cookies['lang'] = 'en'
        self.session.cookies.update(cookies)

    def series_metadata(self, data):
        title = data['title'].strip()
        episode_list = []
        seasons = set()
        for episode in data['entries']:
            if episode and 'season_number' in episode and 'episode_number' in episode:
                episode_list.append(episode)
                seasons.add(episode['season_number'])

        if len(seasons) > 1:
            self.logger.info(
                self._("\n%s total: %s season(s)"), title, len(seasons))
        else:
            self.logger.info("\n%s", title)

        for season_index in seasons:
            episodes = list(filter(
                lambda episode: episode['season_number'] == season_index, episode_list))
            episode_num = len(episodes)

            if self.last_episode:
                episodes = [episodes[-1]]
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                 season_index,
                                 episode_num,
                                 season_index)
            else:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                 season_index,
                                 episode_num)

            name = rename_filename(
                f'{title}.S{str(season_index).zfill(2)}')
            folder_path = os.path.join(self.download_path, name)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            languages = set()
            subtitles = []
            for episode in episodes:
                episode_index = episode['episode_number']
                if not self.download_season or season_index in self.download_season:
                    if not self.download_episode or episode_index in self.download_episode:
                        filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.ass'

                        subs, lang_paths = self.get_subtitle(
                            media_info=episode, folder_path=folder_path, filename=filename)
                        subtitles += subs
                        languages = set.union(languages, lang_paths)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

    def get_subtitle(self, media_info, folder_path, filename):

        lang_paths = set()
        subtitles = []
        available_languages = set()
        if 'subtitles' in media_info and media_info['subtitles']:
            for sub_lang in media_info['subtitles']:
                sub_lang = get_language_code(sub_lang)
                available_languages.add(sub_lang)
                if sub_lang in self.subtitle_language or 'all' in self.subtitle_language:
                    if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                        lang_folder_path = os.path.join(
                            folder_path, sub_lang)
                    else:
                        lang_folder_path = folder_path

                    lang_paths.add(lang_folder_path)

                    os.makedirs(lang_folder_path, exist_ok=True)

                    subtitles.append({
                        'name': filename.replace('.ass', f'.{sub_lang}.ass'),
                        'path': lang_folder_path,
                        'url': next(sub['url'] for sub in media_info['subtitles'][sub_lang] if sub['ext'] == 'ass')
                    })
            get_all_languages(available_languages=available_languages,
                              subtitle_language=self.subtitle_language, locale_=self.locale)
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
        cookie_file = Path(
            config.directories['cookies']) / credentials[self.platform]['cookies']

        match_filter = "language=ja-JP"
        ydl_opts = {
            'cookiefile': cookie_file,
            'http_headers': {'User-Agent': user_agent},
            'match_filter':  yt_dlp.utils.match_filter_func(match_filter),
            'ignoreerrors': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                data = ydl.extract_info(self.url, download=False)
                self.series_metadata(data)
        except yt_dlp.utils.DownloadError as error:
            if 'Request blocked by Cloudflare' in str(error):
                self.logger.error(' - Renew cookies!')
                sys.exit(1)
