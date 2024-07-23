#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Viki
"""

import os
from pathlib import Path
import re
import shutil
import sys
import time
import orjson
from configs.config import config, credentials, user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_all_languages, get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.baseservice import BaseService


class Viki(BaseService):
    """
    Service code for Viki streaming service (https://www.viki.com/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.token = ''

    def movie_metadata(self, data):
        title = data['titles']['en'].strip()
        release_year = data['distributors'][0]['from'][:4]

        self.logger.info("\n%s (%s)", title, release_year)

        if data['blocked'] is True:
            self.logger.error(self._(
                "\nPlease check your subscription plan, and make sure you are able to watch it online!"))
            sys.exit(0)

        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)
        filename = f"{title}.WEB-DL.{self.platform}.vtt"

        languages = set()
        subtitles = []

        media_info = self.get_media_info(
            video_id=data['watch_now']['id'], filename=filename)

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

    def series_metadata(self, data):
        season_index = re.search(r'(.+) Season (\d+)', data['titles']['en'])
        if season_index:
            title = season_index.group(1).strip()
            season_index = int(season_index.group(2))
        else:
            title = data['titles']['en'].strip()
            season_index = 1

        self.logger.info(self._("\n%s Season %s"), title, season_index)

        current_eps = data['episodes']['count']
        episode_num = data['planned_episodes']

        episodes_url = self.config['api']['episodes'].format(
            url=data['episodes']['url']['api'], token=self.token)

        if data['flags']['on_air'] is True:
            episodes_url += f'&watch_schedule=1&ws_end_time={int(time.time())}'

        self.session.headers.update({
            'Referer': 'https://www.viki.com/'
        })
        res = self.session.get(url=episodes_url, timeout=5)

        episodes = []
        if res.ok:
            episodes = res.json()['response']
            self.logger.debug("episodes: %s", episodes)
            if len(episodes) == 0:
                self.logger.error(res.text)
                sys.exit(1)
        else:
            self.logger.error(res.text)
            sys.exit(1)

        name = rename_filename(f'{title}.S{str(season_index).zfill(2)}')
        folder_path = os.path.join(self.download_path, name)

        if self.last_episode:
            episodes = [episodes[-1]]
            self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                             season_index,
                             episode_num,
                             season_index)
        else:
            if current_eps and current_eps != episode_num:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                 season_index, episode_num, current_eps)
            else:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                 season_index,
                                 episode_num)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        languages = set()
        subtitles = []
        for episode in episodes:
            episode_index = int(episode['number'])
            if not self.download_season or season_index in self.download_season:
                if not self.download_episode or episode_index in self.download_episode:
                    filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'

                    if episode['blocked'] is True:
                        self.logger.error(self._(
                            "\nPlease check your subscription plan, and make sure you are able to watch it online!"))
                        break
                    self.logger.info(
                        f"Getting S{str(season_index).zfill(2)}E{str(episode_index).zfill(2)} subtitle...")
                    media_info = self.get_media_info(
                        video_id=episode['id'], filename=filename)
                    subs, lang_paths = self.get_subtitle(
                        media_info=media_info, folder_path=folder_path, filename=filename)
                    if not subs:
                        break
                    subtitles += subs
                    languages = set.union(languages, lang_paths)

        self.download_subtitle(
            subtitles=subtitles, languages=languages, folder_path=folder_path)

    def get_media_info(self, video_id, filename):
        """Get media info"""
        self.session.headers.update({
            'x-viki-app-ver': self.config['vmplayer']['version'],
            'x-client-user-agent': user_agent,
            'x-viki-as-id': self.cookies['session__id']
        })
        media_info_url = self.config['api']['videos'].format(
            video_id=video_id)

        res = self.session.get(url=media_info_url, timeout=5)
        if res.ok:
            data = res.json()
            time.sleep(1)  # Avoid http 429 too many request
            if 'video' in data:
                self.logger.debug("media_info: %s", data)
                return data
            else:
                self.logger.error("%s\nError: %s\n", os.path.basename(
                    filename), data['error'])
        else:
            if res.status_code == 429:
                self.logger.debug(res.text)
                self.logger.error(
                    self._("\nToo Many Requests! Please clear browser cookies and re-download cookies!"))
                os.remove(
                    Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
            sys.exit(1)

    def get_subtitle(self, media_info, folder_path, filename):
        lang_paths = set()
        subtitles = []
        available_languages = set()

        if media_info:
            if 'subtitles' in media_info and media_info['subtitles']:
                for sub in media_info['subtitles']:
                    if sub['percentage'] > 90:
                        sub_lang = get_language_code(sub['srclang'])
                        available_languages.add(sub_lang)
                        if sub_lang in self.subtitle_language or 'all' in self.subtitle_language:
                            if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                                lang_folder_path = os.path.join(
                                    folder_path, sub_lang)
                            else:
                                lang_folder_path = folder_path
                            lang_paths.add(lang_folder_path)

                            os.makedirs(lang_folder_path,
                                        exist_ok=True)

                            subtitles.append({
                                'name': filename.replace('.vtt', f'.{sub_lang}.vtt'),
                                'path': lang_folder_path,
                                'url': sub['src']
                            })

                get_all_languages(available_languages=available_languages,
                                  subtitle_language=self.subtitle_language, locale_=self.locale)
            elif media_info['video']['hardsubs']:
                self.logger.error(
                    self._("\nSorry, there's no embedded subtitles in this video!"))
            else:
                self.logger.error(
                    self._("\nPlease check your subscription plan, and make sure you are able to watch it online!"))

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
        res = self.session.get(url=self.url, timeout=5)

        if res.ok:
            match = re.search(r'({\"props\":{.*})', res.text)
            data = orjson.loads(match.group(1))['props']['pageProps']
            if 'token' not in data['userInfo']:
                self.token = 'undefined'
            else:
                self.token = data['userInfo']['token']
            data = data['containerJson']
            if '/movies' in self.url:
                self.movie_metadata(data)
            else:
                self.series_metadata(data)
        else:
            self.logger.error(res.text)
