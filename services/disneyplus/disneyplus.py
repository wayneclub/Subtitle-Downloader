#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Disney+
"""

import re
import os
import logging
import math
import shutil
import sys
from urllib.parse import urljoin
import m3u8
from configs.config import Platform
from utils.helper import get_locale, download_audio, download_files, fix_filename
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.disneyplus.disneyplus_login import Login
from services.service import Service


class DisneyPlus(Service):

    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.credential = self.config.credential(Platform.DISNEYPLUS)
        self.email = args.email if args.email else self.credential['email']
        self.password = args.password if args.password else self.credential['password']

        self.subtitle_language = args.subtitle_language
        self.language_list = []

        self.audio_language = args.audio_language

        self.profile = dict()
        self.access_token = ''

        self.api = {
            'DmcSeriesBundle': 'https://disney.content.edge.bamgrid.com/svc/content/DmcSeriesBundle/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/encodedSeriesId/{series_id}',
            'DmcEpisodes': 'https://disney.content.edge.bamgrid.com/svc/content/DmcEpisodes/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/seasonId/{season_id}/pageSize/30/page/{page}',
            'DmcVideo': 'https://disney.content.edge.bamgrid.com/svc/content/DmcVideoBundle/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/encodedFamilyId/{family_id}',
            'playback': 'https://disney.playback.edge.bamgrid.com/media/{media_id}/scenarios/tvs-drm-cbcs'
        }

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        if self.subtitle_language != 'all':
            self.language_list = tuple([
                language for language in self.subtitle_language.split(',')])

    def movie_subtitle(self):
        movie_url = self.api['DmcVideo'].format(
            region=self.profile['region'],
            language=self.profile['language'],
            family_id=os.path.basename(self.url))
        res = self.session.get(url=movie_url)
        if res.ok:
            data = res.json()['data']['DmcVideoBundle']['video']
            title = data['text']['title']['full']['program']['default']['content'].strip(
            )
            self.logger.info("\n%s", title)
            title = fix_filename(title)

            folder_path = os.path.join(self.download_path, title)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            program_type = data['programType']
            release_year = next(
                release['releaseYear'] for release in data['releases'] if release['releaseType'] == 'original')

            media_id = data['mediaMetadata']['mediaId']
            m3u8_url = self.get_m3u8_url(media_id)

            file_name = f'{title}.{release_year}.WEB-DL.{Platform.DISNEYPLUS}.vtt'
            subtitle_list, audio_list = self.parse_m3u(m3u8_url)

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

            self.get_subtitle(subtitle_list, program_type,
                              folder_path, file_name)
            if self.audio_language:
                self.get_audio(audio_list, folder_path, file_name)

            convert_subtitle(folder_path=folder_path,
                             platform=Platform.DISNEYPLUS, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)
        else:
            self.logger.error(res.text)

    def series_subtitle(self):
        series_url = self.api['DmcSeriesBundle'].format(
            region=self.profile['region'],
            language=self.profile['language'],
            series_id=os.path.basename(self.url))
        self.logger.debug(series_url)
        res = self.session.get(url=series_url)
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
            title = fix_filename(title)

            for season in seasons:
                season_index = int(season['seasonSequenceNumber'])
                if not self.download_season or season_index in self.download_season:
                    episode_num = season['episodes_meta']['hits']

                    title = self.ripprocess.rename_file_name(
                        f'{title}.S{str(season_index).zfill(2)}')
                    folder_path = os.path.join(self.download_path, title)

                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    self.logger.info(
                        self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                    season_id = season['seasonId']
                    page_size = math.ceil(episode_num / 30)

                    for page in range(1, page_size+1):
                        episode_page_url = self.api['DmcEpisodes'].format(
                            region=self.profile['region'],
                            language=self.profile['language'],
                            season_id=season_id, page=page)
                        self.logger.debug(episode_page_url)
                        episode_res = self.session.get(url=episode_page_url)

                        if episode_res.ok:
                            episode_data = episode_res.json(
                            )['data']['DmcEpisodes']['videos']
                            for episode in episode_data:
                                episode_index = int(
                                    episode['episodeSequenceNumber'])
                                if not self.download_episode or episode_index in self.download_episode:
                                    episode_name = str(episode_index).zfill(2)
                                    program_type = episode['programType']
                                    media_id = episode['mediaMetadata']['mediaId']
                                    m3u8_url = self.get_m3u8_url(media_id)
                                    self.logger.debug(m3u8_url)

                                    file_name = f'{title}E{episode_name}.WEB-DL.{Platform.DISNEYPLUS}.vtt'
                                    subtitle_list, audio_list = self.parse_m3u(
                                        m3u8_url)

                                    if not subtitle_list:
                                        self.logger.error(
                                            "No subtitles found!")
                                        sys.exit(1)

                                    self.logger.info(
                                        self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

                                    self.get_subtitle(subtitle_list, program_type,
                                                      folder_path, file_name)
                                    if self.audio_language:
                                        self.get_audio(
                                            audio_list, folder_path, file_name)

                    convert_subtitle(folder_path=folder_path,
                                     platform=Platform.DISNEYPLUS, lang=self.locale)
                    if self.output:
                        shutil.move(folder_path, self.output)
        else:
            self.logger.error(res.text)

    def get_m3u8_url(self, media_id):
        headers = {
            'accept': 'application/vnd.media-service+json; version=6',
            'User-Agent': self.user_agent,
            'x-bamsdk-platform': "macOS",
            'x-bamsdk-version': '23.1',
            'x-dss-edge-accept': 'vnd.dss.edge+json; version=2',
            'x-dss-feature-filtering': 'true',
            'Origin': 'https://www.disneyplus.com',
            'authorization': self.access_token
        }
        playback_url = self.api['playback'].format(
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
            url=playback_url, headers=headers, json=json_data,)
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

        playlists = m3u8.load(m3u_link).playlists
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

                if not self.language_list or sub_lang in self.language_list:
                    sub = {}
                    sub['lang'] = sub_lang

                    sub_m3u8 = urljoin(media.base_uri, media.uri)
                    sub['urls'] = []
                    if not sub_lang in languages:
                        segments = m3u8.load(sub_m3u8)
                        for uri in segments.files:
                            sub['urls'].append(urljoin(segments.base_uri, uri))
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

        return sub_url_list, audio_url_list

    def get_subtitle(self, subtitle_list, program_type, folder_path, sub_name):

        languages = set()
        subtitles = []

        for sub in subtitle_list:
            file_name = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            if program_type == 'movie' or len(self.language_list) == 1:
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

    def download_subtitle(self, subtitles, languages):
        if subtitles and languages:
            download_files(subtitles)

            display = True
            for lang_path in sorted(languages):
                if 'tmp' in lang_path:
                    merge_subtitle_fragments(
                        folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                    display = False

    def get_audio(self, audio_list, folder_path, audio_name):
        for audio in audio_list:
            if audio['lang'] in ['cmn-TW', 'yue']:
                file_name = audio_name.replace(
                    '.vtt', f".{audio['lang']}{audio['extension']}")
                self.logger.info(
                    self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
                download_audio(audio['url'], os.path.join(
                    folder_path, file_name))

    def main(self):
        self.get_language_list()
        user = Login(email=self.email,
                     password=self.password,
                     ip_info=self.ip_info,
                     locale=self.locale)
        self.profile, self.access_token = user.get_auth_token()
        if self.default_language:
            self.profile['language'] = self.default_language
            # self.profile['language'] = 'en'
        if self.region:
            self.profile['region'] = self.region

        if '/series' in self.url:
            self.series_subtitle()
        elif '/movies' in self.url:
            self.movie_subtitle()
