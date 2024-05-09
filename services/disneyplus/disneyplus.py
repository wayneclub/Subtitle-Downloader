#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Disney+
"""

import os
import math
import shutil
import sys
from urllib.parse import urljoin
import m3u8
import requests
from configs.config import credentials, user_agent
from utils.helper import get_all_languages, get_locale
from utils.io import rename_filename, download_files, download_audio
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.disneyplus.disneyplus_login import Login
from services.baseservice import BaseService


class DisneyPlus(BaseService):
    """
    Service code for DisneyPlus streaming service (https://www.disneyplus.com).

    Authorization: email & password
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.audio_language = args.audio_language
        self.profile = dict()
        self.access_token = ''

    def movie_subtitle(self):
        movie_url = self.config['api']['DmcVideo'].format(
            region=self.profile['region'],
            language=self.profile['language'],
            family_id=os.path.basename(self.url))
        res = self.session.get(url=movie_url, timeout=5)
        if res.ok:
            data = res.json()['data']['DmcVideoBundle']['video']
            title = data['text']['title']['full']['program']['default']['content'].strip(
            )
            release_year = next(
                release['releaseYear'] for release in data['releases'] if release['releaseType'] == 'original')

            self.logger.info("\n%s (%s)", title, release_year)
            title = rename_filename(f'{title}.{release_year}')

            folder_path = os.path.join(self.download_path, title)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            program_type = data['programType']

            media_id = data['mediaMetadata']['mediaId']
            m3u8_url = self.get_m3u8_url(media_id)

            filename = f'{title}.{release_year}.WEB-DL.{self.platform}.vtt'
            subtitle_list, audio_list = self.parse_m3u(m3u8_url)

            if not subtitle_list:
                self.logger.error(
                    self._("\nNo subtitles found!"))
                sys.exit(1)

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), filename)
            self.get_subtitle(subtitle_list, program_type,
                              folder_path, filename)
            if self.audio_language:
                self.get_audio(audio_list, folder_path, filename)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)
        else:
            self.logger.error(res.text)

    def series_subtitle(self):
        series_url = self.config['api']['DmcSeriesBundle'].format(
            region=self.profile['region'],
            language=self.profile['language'],
            series_id=os.path.basename(self.url))
        self.logger.debug(series_url)
        res = self.session.get(url=series_url, timeout=5)
        if res.ok:
            data = res.json()['data']['DmcSeriesBundle']
            if not data['series']:
                self.logger.error("Unable to find series!")
                sys.exit(1)
            title = data['series']['text']['title']['full']['series']['default']['content'].strip(
            )
            seasons = data['seasons']['seasons']

            self.logger.info(self._("\n%s total: %s season(s)"),
                             title, len(seasons))

            for season in seasons:
                season_index = int(season['seasonSequenceNumber'])
                if not self.download_season or season_index in self.download_season:
                    episode_num = season['episodes_meta']['hits']
                    season_id = season['seasonId']
                    episodes = self.get_episodes(
                        season_id=season_id, episode_num=episode_num)

                    name = rename_filename(
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
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         season_index,
                                         episode_num)

                    for episode in episodes:
                        episode_index = episode['episodeSequenceNumber']
                        if not self.download_episode or episode_index in self.download_episode:
                            program_type = episode['programType']
                            media_id = episode['mediaMetadata']['mediaId']
                            m3u8_url = self.get_m3u8_url(media_id)
                            self.logger.debug(m3u8_url)

                            filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'
                            subtitle_list, audio_list = self.parse_m3u(
                                m3u8_url)

                            if not subtitle_list:
                                self.logger.error(
                                    self._("\nNo subtitles found!"))
                                sys.exit(1)

                            self.logger.info(
                                self._("\nDownload: %s\n---------------------------------------------------------------"), filename)
                            self.get_subtitle(subtitle_list, program_type,
                                              folder_path, filename)
                            if self.audio_language:
                                self.get_audio(
                                    audio_list, folder_path, filename)

                    convert_subtitle(folder_path=folder_path,
                                     platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)
        else:
            self.logger.error(res.text)

    def get_episodes(self, season_id, episode_num):
        episodes = []
        page_size = math.ceil(episode_num / 30)
        for page in range(1, page_size+1):
            episode_page_url = self.config['api']['DmcEpisodes'].format(
                region=self.profile['region'],
                language=self.profile['language'],
                season_id=season_id, page=page)
            self.logger.debug(episode_page_url)
            res = self.session.get(url=episode_page_url, timeout=5)

            if res.ok:
                data = res.json()
                episodes += data['data']['DmcEpisodes']['videos']
            else:
                self.logger.error(res.text)
                sys.exit(1)
        return episodes

    def get_m3u8_url(self, media_id):
        headers = {
            'accept': 'application/vnd.media-service+json; version=6',
            'User-Agent': user_agent,
            'x-bamsdk-platform': "macOS",
            'x-bamsdk-version': '23.1',
            'x-dss-edge-accept': 'vnd.dss.edge+json; version=2',
            'x-dss-feature-filtering': 'true',
            'Origin': 'https://www.disneyplus.com',
            'authorization': self.access_token
        }
        playback_url = self.config['api']['playback'].format(
            media_id=media_id)
        self.logger.debug("playback url: %s", playback_url)

        json_data = {
            'playback': {
                'attributes': {
                    'resolution': {
                        'max': [
                            '1920x1080',
                        ],
                    },
                    'protocol': 'HTTPS',
                    'assetInsertionStrategy': 'SGAI',
                    'playbackInitiationContext': 'ONLINE',
                    'frameRates': [
                        60,
                    ],
                    'slugDuration': 'SLUG_500_MS',
                }
            },
        }
        res = self.session.post(
            url=playback_url, headers=headers, json=json_data, timeout=10)
        if res.ok:
            data = res.json()['stream']['sources'][0]['complete']
            self.logger.debug(data)
            return data['url']
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def parse_m3u(self, m3u_link):
        base_url = os.path.dirname(m3u_link)
        sub_url_list = []
        languages = set()
        audio_url_list = []

        headers = {
            'user-agent': user_agent
        }

        playlists = m3u8.load(uri=m3u_link, headers=headers).playlists
        self.logger.debug("playlists: %s", playlists)

        quality_list = [
            playlist.stream_info.bandwidth for playlist in playlists]
        best_quality = quality_list.index(max(quality_list))

        for media in playlists[best_quality].media:
            if media.type == 'SUBTITLES' and media.group_id == 'sub-main':
                if media.language:
                    sub_lang = media.language
                if media.forced == 'YES':
                    sub_lang += '-forced'

                sub = {}
                sub['lang'] = sub_lang
                sub['m3u8_url'] = urljoin(media.base_uri, media.uri)
                languages.add(sub_lang)
                sub_url_list.append(sub)

            if self.audio_language and media.type == 'AUDIO' and not 'Audio Description' in media.name:
                audio = {}
                if media.group_id == 'eac-3':
                    audio['url'] = f'{base_url}/{media.uri}'
                    audio['extension'] = '.eac3'
                elif media.group_id == 'aac-128k':
                    audio['url'] = f'{base_url}/{media.uri}'
                    audio['extension'] = '.aac'
                audio['lang'] = media.language
                self.logger.debug(audio['url'])
                audio_url_list.append(audio)

        get_all_languages(available_languages=languages,
                          subtitle_language=self.subtitle_language, locale_=self.locale)

        subtitle_list = []
        for sub in sub_url_list:
            if sub['lang'] in self.subtitle_language or 'all' in self.subtitle_language:
                subtitle = {}
                subtitle['lang'] = sub['lang']
                subtitle['urls'] = []
                segments = m3u8.load(sub['m3u8_url'])
                for uri in segments.files:
                    subtitle['urls'].append(urljoin(segments.base_uri, uri))
                subtitle_list.append(subtitle)

        return subtitle_list, audio_url_list

    def get_subtitle(self, subtitle_list, program_type, folder_path, sub_name):

        languages = set()
        subtitles = []

        for sub in subtitle_list:
            filename = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            if program_type == 'movie' or (len(self.subtitle_language) == 1 and 'all' not in self.subtitle_language):
                lang_folder_path = os.path.join(
                    folder_path, f"tmp_{filename.replace('.vtt', '.srt')}")
            else:
                lang_folder_path = os.path.join(
                    os.path.join(folder_path, sub['lang']), f"tmp_{filename.replace('.vtt', '.srt')}")

            os.makedirs(lang_folder_path, exist_ok=True)

            languages.add(lang_folder_path)

            for url in sub['urls']:
                subtitle = dict()
                subtitle['name'] = filename
                subtitle['path'] = lang_folder_path
                subtitle['url'] = url
                subtitle['segment'] = True
                subtitles.append(subtitle)

        self.download_subtitle(subtitles, languages)

    def download_subtitle(self, subtitles, languages):
        if subtitles and languages:
            download_files(subtitles)

            display = True
            for lang_path in sorted(languages):
                if 'tmp' in lang_path:
                    merge_subtitle_fragments(
                        folder_path=lang_path, filename=os.path.basename(lang_path.replace('tmp_', '')), subtitle_format=self.subtitle_format, locale=self.locale, display=display)
                    display = False

    def get_audio(self, audio_list, folder_path, audio_name):
        for audio in audio_list:
            if audio['lang'] in ['cmn-TW', 'yue']:
                filename = audio_name.replace(
                    '.vtt', f".{audio['lang']}{audio['extension']}")
                self.logger.info(
                    self._("\nDownload: %s\n---------------------------------------------------------------"), filename)
                download_audio(audio['url'], os.path.join(
                    folder_path, filename))

    def main(self):
        user = Login(email=credentials[self.platform]['email'],
                     password=credentials[self.platform]['password'],
                     locale=self.locale,
                     config=self.config,
                     session=self.session)
        self.profile, self.access_token = user.get_auth_token()
        # self.profile['language'] = 'en'

        self.session.headers.update({
            'authorization': self.access_token
        })

        params = {
            'disableSmartFocus': 'true',
            'enhancedContainersLimit': '12',
            'limit': '24',
        }

        res = self.session.get(
            'https://disney.api.edge.bamgrid.com/explore/v1.2/page/entity-f8879d78-6221-4202-b801-eea1c8277bb4',
            params=params,
            timeout=10
        )

        entity_type = ''
        if res.ok:
            entity_type = 'series' if 'series' in res.text else 'movie'
        else:
            self.logger.error(res.text)
            sys.exit(1)

        # Get old url
        res = requests.get(self.url, timeout=10)
        if res.ok:
            self.url = res.url
        else:
            self.logger.error(res.text)
            sys.exit(1)

        if '/movies' in self.url or entity_type == 'movie':
            self.movie_subtitle()
        else:
            self.series_subtitle()
