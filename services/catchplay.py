#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from CatchPlay
"""
import logging
import os
import re
import shutil
from pathlib import Path
from http.cookiejar import MozillaCookieJar
import orjson
from common.utils import get_locale, import_credential, Platform, http_request, HTTPMethod, get_user_agent, download_files, fix_filename
from common.subtitle import convert_subtitle
from services.service import Service
from tools.xstream.extractor import Extractor
from tools.xstream.downloader import Downloader
from tools.pyshaka.main import parse


class CatchPlay(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        dir_path = os.path.dirname(
            os.path.dirname(__file__)).replace("\\", "/")
        self.config = import_credential()[Platform.CATCHPLAY]
        self.config["cookies_file"] = self.config["cookies_file"].format(
            dir_path=dir_path)
        self.config["cookies_txt"] = self.config["cookies_txt"].format(
            dir_path=dir_path)

        self.access_token = ''
        self.api = {
            'auth': 'https://www.catchplay.com/ssr-oauth/getOauth',
            'play': 'https://hp2-api.catchplay.com/me/play',
            'media_info': 'https://vcmsapi.catchplay.com/video/v3/mediaInfo/{video_id}'
        }

    def get_language_code(self, lang):
        language_code = {
            'zh-TW': 'zh-Hant',
            'en': 'en'
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_cookies(self):
        cookies = None
        if not os.path.isfile(self.config["cookies_file"]):
            try:
                cookiejar = MozillaCookieJar(self.config["cookies_txt"])
                cookiejar.load()
            except Exception:
                print("invalid netscape format cookies file")
                exit()

            cookies = dict()

            for cookie in cookiejar:
                cookies[cookie.name] = cookie.value

            self.save_cookies(cookies)

        with open(self.config["cookies_file"], "rb") as file:
            content = file.read().decode("utf-8")

        if "connect.sid" not in content:
            self.logger.warning("(Some) cookies expired, renew...")
            return cookies

        cookies = orjson.loads(content)["cookies"]
        for cookie in cookies:
            cookie_data = cookies[cookie]
            value = cookie_data[0]
            if cookie != "flwssn":
                cookies[cookie] = value
        if cookies.get("flwssn"):
            del cookies["flwssn"]

        return cookies

    def save_cookies(self, cookies):
        cookie_data = {}
        for name, value in cookies.items():
            cookie_data[name] = [value, 0]
        logindata = {"cookies": cookie_data}
        with open(self.config["cookies_file"], "wb") as file:
            file.write(orjson.dumps(logindata, option=orjson.OPT_INDENT_2))
            file.close()
        os.remove(self.config["cookies_txt"])

    def get_access_token(self, cookies):

        auth_url = self.api['auth']
        data = http_request(session=self.session,
                            url=auth_url, method=HTTPMethod.GET, cookies=cookies)
        self.logger.debug('User: %s', data)
        self.access_token = data['access_token']

    def movie_subtitle(self, data, program_id):
        title = data['apolloState'][f'$Program:{program_id}.title']['local']

        self.logger.info("\n%s", title)
        title = fix_filename(title)

        release_year = data['apolloState'][f'Program:{program_id}']['releaseYear']

        folder_path = os.path.join(self.output, f'{title}.{release_year}')
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        file_name = f'{title}.{release_year}.WEB-DL.{Platform.CATCHPLAY}.vtt'

        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

        play_video_id, play_token = self.get_vcms_access_token(program_id)
        if play_video_id and play_token:
            self.get_subtitle(
                play_video_id, play_token, folder_path, file_name)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.CATCHPLAY, lang=self.locale)

    def series_subtitle(self, data, program_id):
        main_program = 'getMainProgram({\"id\":\"' + program_id + '\"})'
        main_id = data['apolloState']['ROOT_QUERY'][main_program]['id']
        title = data['apolloState'][f'${main_id}.title']['local']
        season_num = data['apolloState'][main_id]['totalChildren']

        self.logger.info(self._("\n%s total: %s season(s)"), title, season_num)
        title = fix_filename(title)

        for season in data['apolloState'][main_id]['children']:
            season_id = season['id']
            season_index = int(
                data['apolloState'][f'${season_id}.title']['short'].replace('S', ''))
            season_name = str(season_index).zfill(2)
            if not self.download_season or season_index == self.download_season:
                folder_path = os.path.join(
                    self.output, f'{title}.S{season_name}')
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                episode_list = data['apolloState'][season_id]['children']
                episode_num = len(episode_list)
                self.logger.info(
                    self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"), season_index, episode_num)

                for episode_index, episode in enumerate(episode_list, start=1):
                    file_name = f'{title}.S{season_name}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.CATCHPLAY}.vtt'
                    self.logger.info(self._("Finding %s ..."), file_name)
                    episode_id = episode['id'].replace('Program:', '')
                    play_video_id, play_token = self.get_vcms_access_token(
                        episode_id)
                    if play_video_id and play_token:
                        self.get_subtitle(
                            play_video_id, play_token, folder_path, file_name)

                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.CATCHPLAY, lang=self.locale)

    def get_vcms_access_token(self, video_id):
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {self.access_token}',
            'user-agent': get_user_agent(),
        }

        payload = {
            'force': False,
            'programType': 'Video',
            'videoId': video_id,
            'watchType': 'movie'
        }

        play_url = self.api['play']
        kwargs = {'json': payload}

        data = http_request(session=self.session,
                            url=play_url, method=HTTPMethod.POST, headers=headers, kwargs=kwargs)
        self.logger.debug(data)

        play_video_id = data['data']['catchplayVideoId']
        play_token = data['data']['playToken']
        return play_video_id, play_token

    def get_subtitle(self, play_video_id, play_token, folder_path, file_name):
        headers = {
            'asiaplay-os-type': 'chrome',
            'asiaplay-device-model': 'mac os',
            'asiaplay-app-version': '3.0',
            'authorization': f'Bearer {play_token}',
            'user-agent': get_user_agent(),
            'asiaplay-platform': 'desktop',
            'asiaplay-os-version': '97.0.4692',
            'asiaplay-device-type': 'web'
        }

        media_info_url = self.api['media_info'].format(video_id=play_video_id)
        data = http_request(session=self.session,
                            url=media_info_url, method=HTTPMethod.GET, headers=headers)

        self.logger.debug('media_info: %s', data)
        if 'subtitleInfo' in data:
            lang_paths = set()
            subtitles = []
            for sub in data['subtitleInfo']:
                sub_lang = self.get_language_code(sub['language'])
                lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)
                subtitle_file_name = file_name.replace(
                    '.vtt', f'.{sub_lang}.vtt')
                subtitle_link = sub['src']
                self.logger.debug(subtitle_link)
                os.makedirs(lang_folder_path,
                            exist_ok=True)
                subtitle = dict()
                subtitle['name'] = subtitle_file_name
                subtitle['path'] = lang_folder_path
                subtitle['url'] = subtitle_link
                subtitles.append(subtitle)

            download_files(subtitles)
        else:
            mpd_url = data['videoUrl']
            self.logger.debug('mpd_url: %s', mpd_url)
            os.makedirs(folder_path,  exist_ok=True)
            self.parse_mpd(mpd_url, folder_path, file_name)

    def parse_mpd(self, url, folder_path, file_name):
        class Attr(object):
            def __init__(self):
                self.proxy = ''
                self.headers = ''
                self.base_url = ''
                self.name = file_name.replace('.vtt', '')
                self.url_patch = ''
                self.live = False
                self.parse_only = False
                self.multi_s = False
                self.select = False
                self.save_dir = Path(folder_path)
                self.limit_per_host = 100
                self.disable_force_close = True
                self.disable_auto_concat = True
                self.disable_auto_decrypt = False
                self.redl_code = []
        args = Attr()
        extractor = Extractor(self.logger, args)
        streams = extractor.fetch_metadata(url)

        for index, stream in enumerate(streams):
            self.logger.debug(
                index, f'{stream.get_name()}{stream.get_init_msg(False)}')

        sub_track_index = next(index for index, stream in enumerate(
            streams) if 'subtitle_WVTT_zh-TW' in f'{stream.get_name()}{stream.get_init_msg(False)}')
        if not sub_track_index:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            exit(1)

        track = [sub_track_index]
        Downloader(self.logger, args).download_streams(streams, track)
        segments_path = os.path.join(
            folder_path, f"{file_name.replace('.vtt', '')}_subtitle_WVTT_zh-TW")
        sub_lang = self.get_language_code(segments_path.split('_')[-1])
        file_name = os.path.join(
            folder_path, file_name.replace(f'.{Platform.CATCHPLAY}', ''))
        self.extract_sub(file_name, sub_lang, segments_path)

    def extract_sub(self, file_name, sub_lang, segments_path):
        class Attr(object):
            def __init__(self):
                self.type = 'wvtt'
                self.init_path = os.path.join(segments_path, 'init.mp4')
                self.segments_path = segments_path
                self.debug = False
                self.segment_time = 0
        args = Attr()
        parse(args)
        os.rename(
            file_name, f'{file_name}.{Platform.CATCHPLAY}.{sub_lang}.vtt')

        os.remove(f"{segments_path.replace('_subtitle_WVTT_zh-TW', '')}.mpd")
        if os.path.exists(segments_path):
            shutil.rmtree(segments_path)

    def download_subtitle(self):
        """Download subtitle from CatchPlay"""

        response = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)
        match = re.search(
            r'<script id=\"__NEXT_DATA__" type=\"application/json\">(.+?)<\/script>', response)
        if match:
            data = orjson.loads(match.group(1).strip())['props']['pageProps']
            program_id = os.path.basename(self.url)
            if data['apolloState'][f'Program:{program_id}']['type'] == 'MOVIE':
                self.movie_subtitle(data, program_id)
            else:
                self.series_subtitle(data, program_id)

    def main(self):
        cookies = self.get_cookies()
        self.get_access_token(cookies)
        self.download_subtitle()
