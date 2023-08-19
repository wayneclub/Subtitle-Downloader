#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from AppleTV+
"""

import logging
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urljoin
import m3u8
import orjson
import requests
from configs.config import Platform
from utils.cookies import Cookies
from utils.helper import get_locale, download_files
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.service import Service


class AppleTVPlus(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.credential = self.config.credential(Platform.APPLETVPLUS)
        self.cookies = Cookies(self.credential)

        self.id = ''
        self.content_type = ''

        self.api = {
            'title': 'https://tv.apple.com/api/uts/v3/{content_type}/{id}',
            'shows': 'https://tv.apple.com/api/uts/v3/shows/{id}/episodes',
            'episode': 'https://tv.apple.com/api/uts/v3/episodes/{id}',
            'configurations': 'https://tv.apple.com/api/uts/v3/configurations'
        }

        self.device = {
            'utscf': 'OjAAAAAAAAA~',
            'utsk': '6e3013c6d6fae3c2::::::ca09fd2bb1996546',
            'caller': 'web',
            'sf': '143470',  # "storefront", country | 143441: US, 143444: GB, 143470:TW
            'v': '68',
            'pfm': 'web',
            'locale': 'zh-Hant',  # en-US
        }

    def get_all_languages(self, available_languages):
        if 'all' in self.subtitle_language:
            self.subtitle_language = available_languages

        intersect = set(self.subtitle_language).intersection(
            set(available_languages))

        if not intersect:
            self.logger.error(
                self._("\nUnsupport %s subtitle, available languages: %s"), ", ".join(self.subtitle_language), ", ".join(available_languages))
            sys.exit(0)

        if len(intersect) != len(self.subtitle_language):
            self.logger.error(
                self._("\nUnsupport %s subtitle, available languages: %s"), ", ".join(set(self.subtitle_language).symmetric_difference(intersect)), ", ".join(available_languages))

    def movie_subtitle(self, data):
        title = data['content']['title']
        release_year = datetime.utcfromtimestamp(
            data['content']['releaseDate'] / 1000).year
        self.logger.info("\n%s (%s)", title, release_year)

        title = self.ripprocess.rename_file_name(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{Platform.APPLETVPLUS}.vtt'
        playable_id = data['smartPlayables'][0]['playableId']
        m3u8_url = data['playables'][playable_id]['assets']['hlsUrl']
        subtitle_list = self.parse_m3u(m3u8_url=m3u8_url)

        if not subtitle_list:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            sys.exit(1)

        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
        self.get_subtitle(
            subtitle_list, folder_path, file_name)

        convert_subtitle(folder_path=folder_path,
                         platform=Platform.APPLETVPLUS, lang=self.locale)
        if self.output:
            shutil.move(folder_path, self.output)

    def series_subtitle(self, data):

        title = data['content']['title']

        seasons = data['howToWatch'][0]['seasons']
        season_num = len(seasons)

        self.logger.info(self._("\n%s total: %s season(s)"), title, season_num)

        for season in seasons:
            season_id = season['id']
            season_index = data['seasons'][season_id]['seasonNumber']
            if season_index == 1:
                params = self.device | {'nextToken': '0:10'}
            elif season_index == 2:
                params = self.device | {'nextToken': '10:10'}
            else:
                self.logger.error("Can't find nextToken!")
                sys.exit()

            res = self.session.get(self.api['shows'].format(
                id=self.id), params=params, timeout=1)
            if res.ok:
                episodes = res.json()['data']['episodes']
            else:
                self.logger.error(res.text)
                sys.exit(1)

            episode_num = len(episodes)

            episodes = list(filter(
                lambda episode: not episode.get('comingSoon'), episodes))
            current_eps = int(episodes[-1]['episodeNumber'])

            if not self.download_season or season_index in self.download_season:

                name = self.ripprocess.rename_file_name(
                    f'{title}.S{str(season_index).zfill(2)}')
                folder_path = os.path.join(self.download_path, name)

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                if self.last_episode:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num,
                                     season_index)

                    episodes = [list(episodes)[-1]]
                else:
                    if current_eps != episode_num:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index, episode_num, current_eps)
                    else:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index,
                                         episode_num)

                for episode in episodes:
                    episode_index = int(episode['episodeNumber'])
                    if not self.download_episode or episode_index in self.download_episode:
                        file_name = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.APPLETVPLUS}.vtt'

                        res = self.session.get(self.api['episode'].format(
                            id=episode['id']), params=self.device, timeout=5)
                        if res.ok:
                            episode_data = res.json()['data']
                            playable_id = episode_data['smartPlayables'][0]['playableId']
                            m3u8_url = episode_data['playables'][playable_id]['assets']['hlsUrl']
                            self.logger.debug("m3u8_url: %s", m3u8_url)
                        else:
                            self.logger.error(res.text)
                            sys.exit(1)

                        subtitle_list = self.parse_m3u(m3u8_url=m3u8_url)

                        if not subtitle_list:
                            self.logger.error(
                                self._("\nSorry, there's no embedded subtitles in this video!"))
                            sys.exit(1)

                        self.logger.info(
                            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
                        self.get_subtitle(
                            subtitle_list, folder_path, file_name)

                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.APPLETVPLUS, lang=self.locale)
                if self.output:
                    shutil.move(folder_path, self.output)

    def parse_m3u(self, m3u8_url):

        sub_url_list = []
        languages = set()
        playlists = m3u8.load(m3u8_url).playlists
        for media in playlists[0].media:
            if media.type == 'SUBTITLES':
                if media.language:
                    sub_lang = self.get_language_code(media.language)
                if media.forced == 'YES':
                    sub_lang += '-forced'

                if media.characteristics:
                    sub_lang += '-sdh'

                sub = {}
                sub['lang'] = sub_lang
                sub['m3u8_url'] = urljoin(media.base_uri, media.uri)
                languages.add(sub_lang)
                sub_url_list.append(sub)

        self.get_all_languages(sorted(languages))

        subtitle_list = []
        for sub in sub_url_list:
            if sub['lang'] in self.subtitle_language:
                subtitle = {}
                subtitle['lang'] = sub['lang']
                subtitle['urls'] = []
                segments = m3u8.load(sub['m3u8_url'])
                for uri in segments.files:
                    subtitle['urls'].append(urljoin(segments.base_uri, uri))
                subtitle_list.append(subtitle)

        return subtitle_list

    def get_subtitle(self, subtitle_list, folder_path, sub_name):

        languages = set()
        subtitles = []

        for sub in subtitle_list:
            file_name = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            if self.content_type == 'movies' or len(self.subtitle_language) == 1:
                lang_folder_path = os.path.join(
                    folder_path, f"tmp_{file_name.replace('.vtt', '.srt')}")
            else:
                lang_folder_path = os.path.join(
                    os.path.join(folder_path, sub['lang']), f"tmp_{file_name.replace('.vtt', '.srt')}")

            os.makedirs(lang_folder_path, exist_ok=True)

            languages.add(lang_folder_path)

            self.logger.debug(file_name, len(sub['urls']))

            for url in sub['urls']:
                subtitle = dict()
                subtitle['name'] = file_name
                subtitle['path'] = lang_folder_path
                subtitle['url'] = url
                subtitle['segment'] = True
                subtitles.append(subtitle)

        self.download_subtitle(subtitles, languages)

    def get_token(self) -> str:
        """Loads environment config data from WEB App's <meta> tag."""
        res = self.session.get('https://tv.apple.com', timeout=1)
        if res.ok:
            env = re.search(
                r'web-tv-app/config/environment"[\s\S]*?content="([^"]+)', res.text)
            if env:
                data = orjson.loads(unquote(env[1]))
                token = data['MEDIA_API']['token']
                self.logger.debug("token: %s", token)
                return token
            else:
                self.logger.error(
                    self._("\nFailed to get AppleTV+ WEB TV App Environment Configuration..."))
                sys.exit(1)
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_configurations(self) -> Optional[dict]:
        """Get configurations"""

        res = self.session.get(
            self.api['configurations'], params=self.device, timeout=1)
        if res.ok:
            configurations = res.json(
            )['data']['applicationProps']['requiredParamsMap']['Default']
            self.logger.debug("configurations: %s", configurations)
            return configurations
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def download_subtitle(self, subtitles, languages):
        if subtitles and languages:
            download_files(subtitles)

            display = True
            for lang_path in sorted(languages):
                if 'tmp' in lang_path:
                    merge_subtitle_fragments(
                        folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                    display = False

    def main(self):
        self.cookies.load_cookies('media-user-token')
        token = self.get_token()

        cookies = self.cookies.get_cookies()

        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Authorization': f'Bearer {token}',
            'media-user-token': cookies['media-user-token'],
            'x-apple-music-user-token': cookies['media-user-token']
        })

        configurations = self.get_configurations()
        if configurations:
            self.device = configurations

        self.session.cookies = requests.utils.cookiejar_from_dict(
            cookies, cookiejar=None, overwrite=True)

        self.id = os.path.basename(self.url.split('?')[0])
        self.content_type = 'movies' if '/movie/' in self.url else 'shows'
        res = self.session.get(self.api['title'].format(
            content_type=self.content_type, id=self.id), params=self.device, timeout=1)
        if res.ok:
            data = res.json()['data']
            if self.content_type == 'movies':
                self.movie_subtitle(data)
            else:
                self.series_subtitle(data)
        else:
            self.logger.error(res.text)
