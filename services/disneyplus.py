"""
This module is to download subtitle from Disney+
"""

import re
import os
import logging
import math
import shutil
from getpass import getpass
import m3u8
import requests
from common.utils import http_request, HTTPMethod, download_audio, convert_subtitle, merge_subtitle, download_file_multithread
from services.disneyplus_login import Login


class DisneyPlus(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url
        self.email = args.email
        self.password = args.password
        if args.output:
            self.output = args.output
        else:
            self.output = os.getcwd()
        if args.season:
            self.download_season = int(args.season)
        else:
            self.download_season = None

        self.subtitle_language = args.subtitle_language
        self.language_list = []

        self.audio_language = args.audio_language

        self.session = requests.Session()

        self.token = ''

        self.api = {
            'DmcSeriesBundle': 'https://disney.content.edge.bamgrid.com/svc/content/DmcSeriesBundle/version/5.1/region/TW/audience/false/maturity/1850/language/zh-Hant/encodedSeriesId/{series_id}',
            'DmcEpisodes': 'https://disney.content.edge.bamgrid.com/svc/content/DmcEpisodes/version/5.1/region/TW/audience/false/maturity/1850/language/zh-Hant/seasonId/{season_id}/pageSize/30/page/{page}',
            'DmcVideo': 'https://disney.content.edge.bamgrid.com/svc/content/DmcVideoBundle/version/5.1/region/TW/audience/false/maturity/1850/language/zh-Hant/encodedFamilyId/{family_id}',
        }

        self.language_code = ('zh-Hant', 'zh-Hans', 'zh-HK', 'da', 'de', 'en', 'es-ES', 'es-419',
                              'fr-FR', 'fr-FR', 'fr-CA', 'it', 'ja', 'ko', 'nl', 'no', 'pt-PT', 'pt-BR', 'fi', 'sv')

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'
        elif self.subtitle_language == 'all':
            self.subtitle_language = ','.join(list(self.language_code))

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def download_subtitle(self):
        if '/series' in self.url:
            series_url = self.api['DmcSeriesBundle'].format(
                series_id=os.path.basename(self.url))
            self.logger.debug(series_url)
            data = http_request(session=self.session, url=series_url, method=HTTPMethod.GET)[
                'data']['DmcSeriesBundle']
            drama_name = data['series']['text']['title']['full']['series']['default']['content'].strip(
            )
            seasons = data['seasons']['seasons']

            self.logger.info('\n%s 共有：%s 季', drama_name, len(seasons))

            for season in seasons:
                season_index = season['seasonSequenceNumber']
                if not self.download_season or season_index == self.download_season:
                    season_name = str(season_index).zfill(2)
                    episode_num = season['episodes_meta']['hits']

                    folder_path = os.path.join(
                        self.output, f'{drama_name}.S{season_name}')

                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    self.logger.info(
                        '\n第 %s 季 共有：%s 集\t下載全集\n---------------------------------------------------------------', season_index, episode_num)

                    season_id = season['seasonId']
                    page_size = math.ceil(episode_num / 30)

                    for page in range(1, page_size+1):
                        episode_page_url = self.api['DmcEpisodes'].format(
                            season_id=season_id, page=page)
                        self.logger.debug(episode_page_url)
                        for episode in http_request(session=self.session, url=episode_page_url, method=HTTPMethod.GET)['data']['DmcEpisodes']['videos']:
                            episode_index = episode['episodeSequenceNumber']
                            episode_name = str(episode_index).zfill(2)
                            program_type = episode['programType']
                            media_id = episode['mediaMetadata']['mediaId']
                            m3u8_url = self.get_m3u8_url(media_id)
                            self.logger.debug(m3u8_url)
                            file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.Disney+.vtt'
                            subtitle_list, audio_list = self.parse_m3u(
                                m3u8_url)
                            self.get_subtitle(subtitle_list, program_type,
                                              folder_path, file_name)
                            if self.audio_language:
                                self.get_audio(
                                    audio_list, folder_path, file_name)

                    convert_subtitle(folder_path, 'disney')

        elif '/movies' in self.url:
            movie_url = self.api['DmcVideo'].format(
                family_id=os.path.basename(self.url))
            data = http_request(session=self.session, url=movie_url, method=HTTPMethod.GET)[
                'data']['DmcVideoBundle']['video']
            movie_name = data['text']['title']['full']['program']['default']['content'].strip(
            )
            self.logger.info('\n%s', movie_name)
            folder_path = os.path.join(self.output, movie_name)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            program_type = data['programType']
            release_year = next(
                release['releaseYear'] for release in data['releases'] if release['releaseType'] == 'original')

            media_id = data['mediaMetadata']['mediaId']
            m3u8_url = self.get_m3u8_url(media_id)

            file_name = f'{movie_name}.{release_year}.WEB-DL.Disney+.vtt'
            subtitle_list, audio_list = self.parse_m3u(m3u8_url)
            self.get_subtitle(subtitle_list, program_type,
                              folder_path, file_name)
            if self.audio_language:
                self.get_audio(audio_list, folder_path, file_name)

            convert_subtitle(folder_path, 'disney')

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
        playback_url = f'https://disney.playback.edge.bamgrid.com/media/{media_id}/scenarios/restricted-drm-ctr-sw'
        self.logger.debug(playback_url)
        respones = http_request(
            session=self.session, url=playback_url, method=HTTPMethod.GET, headers=headers)
        return respones['stream']['complete']

    def parse_m3u(self, m3u_link):
        base_url = os.path.dirname(m3u_link)
        sub_url_list = []
        audio_url_list = []

        playlists = m3u8.load(m3u_link).playlists
        quality_list = [
            playlist.stream_info.bandwidth for playlist in playlists]
        best_quality = quality_list.index(max(quality_list))

        self.logger.debug('best_quality: %s',
                          playlists[best_quality].stream_info)

        for media in playlists[best_quality].media:
            if media.type == 'SUBTITLES' and media.group_id == 'sub-main' and not 'forced' in media.name:
                sub = {}
                sub['lang'] = media.language
                m3u_sub = m3u8.load(os.path.join(base_url, media.uri))
                sub['urls'] = []
                for segement in re.findall(r'.+\-MAIN\/.+\.vtt', m3u_sub.dumps()):
                    sub['urls'].append(os.path.join(
                        f'{base_url}/r/', segement))
                sub_url_list.append(sub)
            if media.type == 'AUDIO' and not 'Audio Description' in media.name:
                audio = {}
                if media.group_id == 'eac-3':
                    audio['url'] = os.path.join(base_url, media.uri)
                    audio['extension'] = '.eac3'
                elif media.group_id == 'aac-128k':
                    audio['url'] = os.path.join(base_url, media.uri)
                    audio['extension'] = '.aac'
                audio['lang'] = media.language
                audio_url_list.append(audio)
        return sub_url_list, audio_url_list

    def get_subtitle(self, subtitle_list, program_type, folder_path, sub_name):
        available_languages = tuple(
            [sub['lang'] for sub in subtitle_list])
\
        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error('提供的字幕語言：%s', available_languages)
            exit()

        for sub in subtitle_list:
            if sub['lang'] in self.language_list:
                file_name=sub_name.replace('.vtt', f".{sub['lang']}.srt")
                self.logger.info('\n下載：%s\n---------------------------------------------------------------', file_name)

                tmp_folder_path=os.path.join(
                    os.path.join(folder_path, sub['lang']), 'tmp')
                if program_type == 'movie' or len(self.language_list) == 1:
                    tmp_folder_path=os.path.join(folder_path, 'tmp')

                if os.path.exists(tmp_folder_path):
                    shutil.rmtree(tmp_folder_path)
                os.makedirs(tmp_folder_path, exist_ok = True)
                subtitle_names = [os.path.basename(url) for url in sub['urls']]
                download_file_multithread(sub['urls'], subtitle_names, tmp_folder_path)
                convert_subtitle(tmp_folder_path)
                merge_subtitle(tmp_folder_path, file_name)

    def get_audio(self, audio_list, folder_path, audio_name):
        for audio in audio_list:
            if audio['lang'] in ['cmn-TW', 'yue']:
                file_name=audio_name.replace(
                    '.vtt', f".{audio['lang']}{audio['extension']}")
                self.logger.info('\n下載：%s', file_name)
                download_audio(audio['url'], os.path.join(
                    folder_path, file_name))

    def main(self):
        self.get_language_list()
        if self.email and self.password:
            email=self.email
            password=self.password
        else:
            email=input('輸入帳號：')
            password=getpass('輸入密碼（不顯示）：')
        user=Login(email = email, password = password)
        self.token=user.get_auth_token()
        self.download_subtitle()
