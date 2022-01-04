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
import m3u8
from common.utils import Platform, get_locale, http_request, HTTPMethod, download_audio, download_files
from common.subtitle import convert_subtitle, merge_subtitle_fragments
from services.disneyplus_login import Login
from services.service import Service


class DisneyPlus(Service):

    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.email = args.email
        self.password = args.password

        self.subtitle_language = args.subtitle_language
        self.language_list = []

        self.audio_language = args.audio_language

        self.profile = dict()
        self.token = ''

        self.api = {
            'DmcSeriesBundle': 'https://disney.content.edge.bamgrid.com/svc/content/DmcSeriesBundle/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/encodedSeriesId/{series_id}',
            'DmcEpisodes': 'https://disney.content.edge.bamgrid.com/svc/content/DmcEpisodes/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/seasonId/{season_id}/pageSize/30/page/{page}',
            'DmcVideo': 'https://disney.content.edge.bamgrid.com/svc/content/DmcVideoBundle/version/5.1/region/{region}/audience/false/maturity/1850/language/{language}/encodedFamilyId/{family_id}',
            'playback': 'https://disney.playback.edge.bamgrid.com/media/{media_id}/scenarios/restricted-drm-ctr-sw'
            # 'playback': 'https://disney.playback.edge.bamgrid.com/media/{media_id}/scenarios/tv-drm-ctr'
        }

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def download_subtitle(self):
        if '/series' in self.url:
            series_url = self.api['DmcSeriesBundle'].format(
                region=self.profile['country'],
                language=self.profile['language'],
                series_id=os.path.basename(self.url))
            self.logger.debug(series_url)
            data = http_request(session=self.session, url=series_url, method=HTTPMethod.GET)[
                'data']['DmcSeriesBundle']
            title = data['series']['text']['title']['full']['series']['default']['content'].strip(
            )
            seasons = data['seasons']['seasons']

            self.logger.info(self._("\n%s total: %s season(s)"),
                             title, len(seasons))

            for season in seasons:
                season_index = season['seasonSequenceNumber']
                if not self.download_season or season_index == self.download_season:
                    season_name = str(season_index).zfill(2)
                    episode_num = season['episodes_meta']['hits']

                    folder_path = os.path.join(
                        self.output, f'{title}.S{season_name}')

                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    self.logger.info(
                        self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                    season_id = season['seasonId']
                    page_size = math.ceil(episode_num / 30)

                    for page in range(1, page_size+1):
                        episode_page_url = self.api['DmcEpisodes'].format(
                            region=self.profile['country'],
                            language=self.profile['language'],
                            season_id=season_id, page=page)
                        self.logger.debug(episode_page_url)
                        episode_data = http_request(
                            session=self.session, url=episode_page_url, method=HTTPMethod.GET)['data']['DmcEpisodes']['videos']
                        for episode in episode_data:
                            episode_index = episode['episodeSequenceNumber']
                            episode_name = str(episode_index).zfill(2)
                            program_type = episode['programType']
                            media_id = episode['mediaMetadata']['mediaId']
                            m3u8_url = self.get_m3u8_url(media_id)
                            self.logger.debug(m3u8_url)

                            file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.Disney+.vtt'
                            subtitle_list, audio_list = self.parse_m3u(
                                m3u8_url)

                            self.logger.info(
                                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

                            self.get_subtitle(subtitle_list, program_type,
                                              folder_path, file_name)
                            if self.audio_language:
                                self.get_audio(
                                    audio_list, folder_path, file_name)

                    convert_subtitle(folder_path=folder_path,
                                     platform=Platform.DISNEY, lang=self.locale)

        elif '/movies' in self.url:
            movie_url = self.api['DmcVideo'].format(
                region=self.profile['country'],
                language=self.profile['language'],
                family_id=os.path.basename(self.url))
            data = http_request(session=self.session, url=movie_url, method=HTTPMethod.GET)[
                'data']['DmcVideoBundle']['video']
            title = data['text']['title']['full']['program']['default']['content'].strip(
            )
            self.logger.info("\n%s", title)
            folder_path = os.path.join(self.output, title)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            program_type = data['programType']
            release_year = next(
                release['releaseYear'] for release in data['releases'] if release['releaseType'] == 'original')

            media_id = data['mediaMetadata']['mediaId']
            m3u8_url = self.get_m3u8_url(media_id)

            file_name = f'{title}.{release_year}.WEB-DL.Disney+.vtt'
            subtitle_list, audio_list = self.parse_m3u(m3u8_url)

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

            self.get_subtitle(subtitle_list, program_type,
                              folder_path, file_name)
            if self.audio_language:
                self.get_audio(audio_list, folder_path, file_name)

            convert_subtitle(folder_path=folder_path,
                             platform=Platform.DISNEY, lang=self.locale)

    def get_m3u8_url(self, media_id):
        headers = {
            "accept": "application/vnd.media-service+json; version=2",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
            "Sec-Fetch-Mode": "cors",
            "x-bamsdk-platform": "macosx",
            "x-bamsdk-version": '3.10',
            "Origin": 'https://www.disneyplus.com',
            "authorization": self.token
        }
        playback_url = self.api['playback'].format(
            media_id=media_id)
        self.logger.debug(playback_url)
        respones = http_request(
            session=self.session, url=playback_url, method=HTTPMethod.GET, headers=headers)
        return respones['stream']['complete']

    def get_all_languages(self, data):
        available_languages = []
        for lang, forced in re.findall(
                r'.+TYPE=SUBTITLES.+LANGUAGE=\"([^\"]+)\".+,FORCED=(.+),', data):
            if forced == 'YES':
                lang += '-forced'
            available_languages.append(lang)

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            exit(0)

    def parse_m3u(self, m3u_link):
        base_url = os.path.dirname(m3u_link)
        playlist = http_request(session=self.session,
                                url=m3u_link, method=HTTPMethod.GET, raw=True)

        self.get_all_languages(playlist)

        sub_url_list = []
        for subtitle in re.findall(r'.+TYPE=SUBTITLES,GROUP-ID=\"sub-main\".+', playlist):
            subtitle_tag = re.search(
                r'LANGUAGE=\"(.+)\",.+,FORCED=(NO|YES).*,URI=\"(.+)\"', subtitle)

            forced = subtitle_tag.group(2)
            if forced == 'YES':
                sub_lang = subtitle_tag.group(1) + '-forced'
            else:
                sub_lang = subtitle_tag.group(1)

            media_uri = subtitle_tag.group(3)

            if sub_lang in self.language_list:
                sub = {}
                sub['lang'] = sub_lang

                sub_m3u8 = f'{base_url}/{media_uri}'
                self.logger.debug(sub_m3u8)
                m3u8_data = http_request(
                    session=self.session, url=sub_m3u8, method=HTTPMethod.GET, raw=True)

                sub['urls'] = []
                for segement in re.findall(r'.+\-MAIN\/.+\.vtt', m3u8_data):
                    sub_url = f'{base_url}/r/{segement}'
                    self.logger.debug(sub_url)
                    sub['urls'].append(sub_url)
                sub_url_list.append(sub)

        audio_url_list = []
        if self.audio_language:
            playlists = m3u8.loads(playlist).playlists
            quality_list = [
                playlist.stream_info.bandwidth for playlist in playlists]
            best_quality = quality_list.index(max(quality_list))

            self.logger.debug('best_quality: %s',
                              playlists[best_quality].stream_info)

            for media in playlists[best_quality].media:
                if media.type == 'AUDIO' and not 'Audio Description' in media.name:
                    audio = {}
                    if media.group_id == 'eac-3':
                        audio['url'] = f'{base_url}/{media.uri}'
                        audio['extension'] = '.eac3'
                    elif media.group_id == 'aac-128k':
                        audio['url'] = f'{base_url}/{media.uri}'
                        audio['extension'] = '.aac'
                    audio['lang'] = media.language
                    audio_url_list.append(audio)

        return sub_url_list, audio_url_list

    # def parse_m3u(self, m3u_link):
    #     base_url = os.path.dirname(m3u_link)
    #     sub_url_list = []
    #     audio_url_list = []

    #     playlists = m3u8.load(m3u_link).playlists
    #     quality_list = [
    #         playlist.stream_info.bandwidth for playlist in playlists]
    #     best_quality = quality_list.index(max(quality_list))

    #     self.logger.debug('best_quality: %s',
    #                       playlists[best_quality].stream_info)

    #     for media in playlists[best_quality].media:
    #         if media.type == 'SUBTITLES' and media.group_id == 'sub-main' and not 'forced' in media.name:
    #             sub = {}
    #             sub['lang'] = media.language
    #             m3u_sub = m3u8.load(os.path.join(base_url, media.uri))
    #             sub['urls'] = []
    #             for segement in re.findall(r'.+\-MAIN\/.+\.vtt', m3u_sub.dumps()):
    #                 sub['urls'].append(os.path.join(
    #                     f'{base_url}/r/', segement))
    #             sub_url_list.append(sub)
    #         if media.type == 'AUDIO' and not 'Audio Description' in media.name:
    #             audio = {}
    #             if media.group_id == 'eac-3':
    #                 audio['url'] = os.path.join(base_url, media.uri)
    #                 audio['extension'] = '.eac3'
    #             elif media.group_id == 'aac-128k':
    #                 audio['url'] = os.path.join(base_url, media.uri)
    #                 audio['extension'] = '.aac'
    #             audio['lang'] = media.language
    #             audio_url_list.append(audio)
    #     return sub_url_list, audio_url_list

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
        user = Login(email=self.email, password=self.password,
                     locale=self.locale)
        self.profile, self.token = user.get_auth_token()
        self.download_subtitle()
