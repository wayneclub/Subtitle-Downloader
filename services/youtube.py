#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from YouTube
"""

import os
from pathlib import Path
import re
import sys
from cn2an import cn2an
import yt_dlp
from yt_dlp.utils import DownloadError
from services.baseservice import BaseService
from utils.helper import get_all_languages, get_language_code, get_locale
from utils.io import download_files, rename_filename
from utils.subtitle import convert_subtitle
from configs.config import config, credentials, user_agent


class YouTube(BaseService):
    """
    Service code for YouTube streaming service (https://www.youtube.com/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def movie_metadata(self, data):
        title = data['title'].replace(
            '《', '').replace('》', '').replace('(', '').replace(')', '').replace('【', '').replace('】', '')
        title = title.split('|')[0].strip()

        release_year = ''
        movie_info = self.get_title_info(
            title=title, title_aliases=[title], is_movie=True)
        if movie_info:
            release_year = movie_info['release_date'][:4]

        if release_year:
            self.logger.info("\n%s (%s)", title, release_year)
        else:
            self.logger.info("\n%s", title)

        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)
        filename = f"{title}.WEB-DL.{self.platform}.vtt"

        languages = set()
        subtitles = []

        subs, lang_paths = self.get_subtitle(
            media_info=data, folder_path=folder_path, filename=filename)
        subtitles += subs
        languages = set.union(languages, lang_paths)

        if subtitles:
            self.logger.info(
                self._(
                    "\nDownload: %s\n---------------------------------------------------------------"),
                filename)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

    def series_metadata(self, data):
        title = data['title'].replace(
            '《', '').replace('》', '').replace('(', '').replace(')', '').replace('【', '').replace('】', '')
        title = title.split('|')[0].strip()
        if re.search(r'[\u4E00-\u9FFF]', title):
            season_search = re.search(
                r'(.+?)第(.+?)[季|彈]', title)
            if season_search:
                title = season_search.group(1).strip()
                season_index = int(season_search.group(2)) if season_search.group(
                    2).isdigit else int(cn2an(season_search.group(2)))
            else:
                season_index = 1
        else:
            season_index = re.search(r'(.+?)[s|S](eason)*( )*(\d+)', title)
            if season_index:
                title = season_index.group(1).strip()
                season_index = int(season_index.group(4))
            else:
                season_index = 1

        self.logger.info(self._("\n%s Season %s"), title, season_index)

        name = rename_filename(f'{title}.S{str(season_index).zfill(2)}')
        folder_path = os.path.join(self.download_path, name)

        episodes = []
        for episode in data['entries']:
            if not '預告' in episode.get('title'):
                if re.search(r'[\u4E00-\u9FFF]', episode['title']):
                    episode_index = re.search(r'第(.+?)[集|話]', episode['title'])
                    if episode_index:
                        episode_index = int(episode_index.group(1)) if episode_index.group(
                            1).isdigit() else cn2an(episode_index.group(1))
                    else:
                        episode_index = re.search(
                            r'.+?#(\d+)', episode['title'])
                        if episode_index:
                            episode_index = int(episode_index.group(1))
                else:
                    episode_index = re.search(
                        r'(.+?)[e|E](pisode)*( )*(\d+)', episode['title'])
                    if episode_index:
                        episode_index = int(episode_index.group(4))

            if episode_index:
                episode['episode_index'] = episode_index
                episodes.append(episode)

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

        languages = set()
        subtitles = []
        for episode in episodes:
            episode_index = episode['episode_index']
            if not self.download_season or season_index in self.download_season:
                if not self.download_episode or episode_index in self.download_episode:
                    filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'

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
                if media_info['subtitles'].get(get_language_code(sub_lang)):
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
                        'name': filename.replace('.vtt', f'.{sub_lang}.vtt'),
                        'path': lang_folder_path,
                        'url': next(sub['url'] for sub in media_info['subtitles'][sub_lang] if sub['ext'] == 'vtt')
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

        ydl_opts = {
            'cookiefile': cookie_file,
            'http_headers': {'User-Agent': user_agent},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                data = ydl.extract_info(self.url, download=False)

            if data.get('_type') == 'playlist':
                self.series_metadata(data)
            else:
                self.movie_metadata(data)
        except DownloadError:
            sys.exit(0)
