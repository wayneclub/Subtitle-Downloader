#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from AppleTV+
"""

import math
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urljoin
import m3u8
import orjson
from configs.config import user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_all_languages, get_language_code, get_locale
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.service import Service


class AppleTVPlus(Service):
    """
    Service code for Apple's TV Plus streaming service (https://tv.apple.com).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.title_id = os.path.basename(self.url.split('?')[0])
        self.content_type = 'movies' if '/movie/' in self.url else 'shows'

    def movie_subtitle(self, data):
        title = data['content']['title']
        release_year = datetime.utcfromtimestamp(
            data['content']['releaseDate'] / 1000).year
        self.logger.info("\n%s (%s)", title, release_year)

        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        filename = f'{title}.WEB-DL.{self.platform}.vtt'
        playable_id = data['smartPlayables'][-1]['playableId']

        m3u8_url = ''
        if data['playables'][playable_id].get('assets'):
            m3u8_url = data['playables'][playable_id]['assets']['hlsUrl']
        elif data['playables'][playable_id].get('itunesMediaApiData'):
            hd_item = next(item for item in data['playables'][playable_id]['itunesMediaApiData']
                           ['offers'] if item['kind'] == 'rent' and item['variant'] == 'HD')
            if hd_item:
                m3u8_url = hd_item['hlsUrl']

        if not m3u8_url:
            self.logger.error(
                self._("\nSorry, you haven't purchased this movie!"))
            sys.exit(0)

        subtitle_list = self.parse_m3u(m3u8_url=m3u8_url)

        if not subtitle_list:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            sys.exit(0)

        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), filename)
        self.get_subtitle(
            subtitle_list, folder_path, filename)

        convert_subtitle(folder_path=folder_path,
                         platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def series_subtitle(self, data):

        title = data['content']['title']

        seasons = data['howToWatch'][0]['seasons']
        season_num = len(seasons)

        self.logger.info(self._("\n%s total: %s season(s)"), title, season_num)

        params = self.config['device'] | {'selectedSeasonEpisodesOnly': False}
        res = self.session.get(self.config['api']['shows'].format(
            id=self.title_id), params=params, timeout=5)
        if res.ok:
            total = res.json()['data']['totalEpisodeCount']
        else:
            self.logger.error(res.text)
            sys.exit(1)

        pages = math.ceil(total / 10)

        next_tokens = [f'{(n)*10}:10' for n in range(pages)]

        episode_list = []
        for next_token in next_tokens:
            params = self.config['device'] | {'nextToken': next_token}

            res = self.session.get(self.config['api']['shows'].format(
                id=self.title_id), params=params, timeout=5)
            if res.ok:
                episode_list += res.json()['data']['episodes']
            else:
                self.logger.error(res.text)
                sys.exit(1)

        for season in seasons:
            season_id = season['id']
            season_index = data['seasons'][season_id]['seasonNumber']

            if not self.download_season or season_index in self.download_season:
                episodes = list(filter(
                    lambda episode: episode['seasonNumber'] == season_index, episode_list))
                episode_num = len(episodes)

                if self.last_episode:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num,
                                     season_index)

                    episodes = [list(filter(
                        lambda episode: not episode.get('comingSoon'), episodes))[-1]]
                else:
                    if filter(lambda episode: episode.get('comingSoon'), episodes):
                        current_eps = int(list(filter(lambda episode: not episode.get(
                            'comingSoon'), episodes))[-1]['episodeNumber'])

                    if current_eps and current_eps != episode_num:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index, episode_num, current_eps)
                    else:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index,
                                         episode_num)

                name = rename_filename(
                    f'{title}.S{str(season_index).zfill(2)}')
                folder_path = os.path.join(self.download_path, name)

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                for episode in episodes:
                    if episode.get('comingSoon'):
                        continue

                    episode_index = episode['episodeNumber']
                    if not self.download_episode or episode_index in self.download_episode:
                        filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'

                        res = self.session.get(self.config['api']['episode'].format(
                            id=episode['id']), params=self.config['device'], timeout=5)
                        if res.ok:
                            episode_data = res.json()['data']
                            playable_id = episode_data['smartPlayables'][-1]['playableId']
                            m3u8_url = episode_data['playables'][playable_id]['assets']['hlsUrl']
                            self.logger.debug("m3u8_url: %s", m3u8_url)
                        else:
                            self.logger.error(res.text)
                            sys.exit(1)

                        subtitle_list = self.parse_m3u(
                            m3u8_url=m3u8_url)

                        if not subtitle_list:
                            self.logger.error(
                                self._("\nSorry, there's no embedded subtitles in this video!"))
                            sys.exit(1)

                        self.logger.info(
                            self._("\nDownload: %s\n---------------------------------------------------------------"), filename)
                        self.get_subtitle(
                            subtitle_list, folder_path, filename)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def parse_m3u(self, m3u8_url):

        sub_url_list = []
        languages = set()
        playlists = m3u8.load(m3u8_url).playlists
        for media in playlists[0].media:
            if media.type == 'SUBTITLES':
                if media.language:
                    sub_lang = get_language_code(media.language)
                if media.forced == 'YES':
                    sub_lang += '-forced'

                if media.characteristics:
                    sub_lang += '-sdh'

                sub = {}
                sub['lang'] = sub_lang
                sub['m3u8_url'] = urljoin(media.base_uri, media.uri)
                languages.add(sub_lang)
                sub_url_list.append(sub)

        get_all_languages(available_languages=languages,
                          subtitle_language=self.subtitle_language, locale_=self.locale)

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
            filename = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            if self.content_type == 'movies' or len(self.subtitle_language) == 1:
                lang_folder_path = os.path.join(
                    folder_path, f"tmp_{filename.replace('.vtt', '.srt')}")
            else:
                lang_folder_path = os.path.join(
                    os.path.join(folder_path, sub['lang']), f"tmp_{filename.replace('.vtt', '.srt')}")

            os.makedirs(lang_folder_path, exist_ok=True)

            languages.add(lang_folder_path)

            self.logger.debug(filename, len(sub['urls']))

            for url in sub['urls']:
                subtitle = dict()
                subtitle['name'] = filename
                subtitle['path'] = lang_folder_path
                subtitle['url'] = url
                subtitle['segment'] = True
                subtitles.append(subtitle)

        self.download_subtitle(subtitles, languages)

    def get_token(self) -> str:
        """Loads environment config data from WEB App's <meta> tag."""
        res = self.session.get('https://tv.apple.com', timeout=5)
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
            self.config['api']['configurations'], params=self.config['device'], timeout=5)
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
                        folder_path=lang_path, filename=os.path.basename(lang_path.replace('tmp_', '')), subtitle_format=self.subtitle_format, locale=self.locale, display=display)
                    display = False

    def main(self):
        token = self.get_token()

        self.session.headers.update({
            'User-Agent': user_agent,
            'Authorization': f'Bearer {token}',
            'media-user-token': self.cookies['media-user-token'],
            'x-apple-music-user-token': self.cookies['media-user-token']
        })

        configurations = self.get_configurations()
        if configurations:
            self.config['device'] = configurations

        res = self.session.get(self.config['api']['title'].format(
            content_type=self.content_type, id=self.title_id), params=self.config['device'], timeout=5)
        if res.ok:
            data = res.json()['data']
            if self.content_type == 'movies':
                self.movie_subtitle(data)
            else:
                self.series_subtitle(data)
        else:
            self.logger.error(res.text)
