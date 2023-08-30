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
from configs.config import credentials, user_agent
from utils.helper import get_locale, download_audio, download_files, fix_filename
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.disneyplus.disneyplus_login import Login
from services.service import Service


class DisneyPlus(Service):
    """
    Service code for DisneyPlus streaming service (https://www.disneyplus.com).

    Authorization: email & password
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

        self.email = args.email if args.email else credentials[self.platform]['email']
        self.password = args.password if args.password else credentials[
            self.platform]['password']

        self.audio_language = args.audio_language

        self.profile = dict()
        self.access_token = ''

    def get_all_languages(self, available_languages):
        """Get all subtitles language"""

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

    def movie_subtitle(self):
        movie_url = self.config['api']['DmcVideo'].format(
            region=self.profile['region'],
            language=self.profile['language'],
            family_id=os.path.basename(self.url))
        res = self.session.get(url=movie_url)
        if res.ok:
            data = res.json()['data']['DmcVideoBundle']['video']
            title = data['text']['title']['full']['program']['default']['content'].strip(
            )
            release_year = next(
                release['releaseYear'] for release in data['releases'] if release['releaseType'] == 'original')

            self.logger.info("\n%s (%s)", title, release_year)
            title = fix_filename(title)

            folder_path = os.path.join(self.download_path, title)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            program_type = data['programType']

            media_id = data['mediaMetadata']['mediaId']
            m3u8_url = self.get_m3u8_url(media_id)

            file_name = f'{title}.{release_year}.WEB-DL.{self.platform}.vtt'
            subtitle_list, audio_list = self.parse_m3u(m3u8_url)

            if not subtitle_list:
                self.logger.error(
                    self._("\nNo subtitles found!"))
                sys.exit(1)

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
            self.get_subtitle(subtitle_list, program_type,
                              folder_path, file_name)
            if self.audio_language:
                self.get_audio(audio_list, folder_path, file_name)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)
        else:
            self.logger.error(res.text)

    def series_subtitle(self):
        series_url = self.config['api']['DmcSeriesBundle'].format(
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
                    season_id = season['seasonId']
                    episodes = self.get_episodes(
                        season_id=season_id, episode_num=episode_num)

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

                            file_name = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'
                            subtitle_list, audio_list = self.parse_m3u(
                                m3u8_url)

                            if not subtitle_list:
                                self.logger.error(
                                    self._("\nNo subtitles found!"))
                                sys.exit(1)

                            self.logger.info(
                                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)
                            self.get_subtitle(subtitle_list, program_type,
                                              folder_path, file_name)
                            if self.audio_language:
                                self.get_audio(
                                    audio_list, folder_path, file_name)

                    convert_subtitle(folder_path=folder_path,
                                     platform=self.platform, lang=self.locale)
                    if self.output:
                        shutil.move(folder_path, self.output)
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
            res = self.session.get(url=episode_page_url)

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

        self.get_all_languages(languages)

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

        return subtitle_list, audio_url_list

    def get_subtitle(self, subtitle_list, program_type, folder_path, sub_name):

        languages = set()
        subtitles = []

        for sub in subtitle_list:
            file_name = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            if program_type == 'movie' or len(self.subtitle_language) == 1:
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
        user = Login(email=self.email,
                     password=self.password,
                     ip_info=self.ip_info,
                     locale=self.locale)
        self.profile, self.access_token = user.get_auth_token()
        # self.profile['language'] = 'en'
        if self.region:
            self.profile['region'] = self.region

        if '/series' in self.url:
            self.series_subtitle()
        elif '/movies' in self.url:
            self.movie_subtitle()
