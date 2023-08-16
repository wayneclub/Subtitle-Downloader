#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from iq.com
"""

from hashlib import md5
import math
import re
import os
from shlex import quote
import shutil
import logging
import subprocess
import sys
from time import time
from urllib.parse import urlencode
import orjson
from cn2an import cn2an
from configs.config import Platform
from utils.cookies import Cookies
from utils.helper import get_locale, download_files
from utils.subtitle import convert_subtitle
from services.service import Service


class IQIYI(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)
        self.subtitle_language = args.subtitle_language

        self.credential = self.config.credential(Platform.IQIYI)
        self.cookies = Cookies(self.credential)

        self.language_list = ()

        self.api = {
            'episode_list': 'https://pcw-api.iq.com/api/episodeListSource/{album_id}?platformId=3&modeCode={mode_code}&langCode={lang_code}&deviceId=21fcb553c8e206bb515b497bb6376aa4&endOrder={end_order}&startOrder={start_order}',
            'meta': 'https://meta.video.iqiyi.com'
        }

    def get_language_code(self, lang):
        language_code = {
            '英語': 'en',
            '繁體中文': 'zh-Hant',
            '簡體中文': 'zh-Hans',
            '韓語': 'ko',
            '馬來語': 'ms',
            '越南語': 'vi',
            '泰語': 'th',
            '印尼語': 'id',
            '阿拉伯語': 'ar',
            '西班牙語': 'es',
            '葡萄牙語': 'pt',
            'Traditional Chinese': 'zh-Hant',
            'Simplified Chinese':  'zh-Hans',
            'Bahasa Malaysia': 'ms',
            'Thai': 'th',
            'Vietnamese': 'vi',
            'Bahasa Indonesia': 'id',
            'English': 'en',
            'Korean': 'ko',
            'Arabic': 'ar',
            'Spanish': 'es',
            'Portuguese': 'pt',
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def get_all_languages(self, data):

        if not 'stl' in data:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            sys.exit(0)

        available_languages = tuple(
            [self.get_language_code(sub['_name']) for sub in data['stl']])

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            sys.exit(0)

    def get_vid(self, play_url):
        vid = ''

        res = self.session.get(play_url)
        if res.ok:
            match = re.search(r'({\"props\":{.*})', res.text)

            if not match:
                self.logger.error("Please input correct play url!")
                sys.exit(1)

            data = orjson.loads(match.group(1))
            vid = data['props']['initialState']['play']['curVideoInfo']['vid']
        else:
            self.logger.error(res.text)
            sys.exit(1)

        if not vid:
            self.logger.error("Can't find vid!")
            sys.exit(1)

        return vid

    def movie_subtitle(self, data):

        title = data['name'].strip()
        release_year = data['year']
        self.logger.info("\n%s (%s)", title, release_year)

        title = self.ripprocess.rename_file_name(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{Platform.IQIYI}.vtt'

        self.logger.info(self._(
            "\nDownload: %s\n---------------------------------------------------------------"), file_name)

        play_url = f"https:{data['playUrl']}"
        vid = self.get_vid(play_url)
        tvid = data['qipuId']
        dash_url = self.get_dash_url(
            vid=vid, tvid=tvid)
        self.logger.debug("dash url: %s", dash_url)

        res = self.session.get(url=dash_url)
        if res.ok:
            movie_data = res.json()['data']
            languages = set()
            subtitles = []
            if 'program' in movie_data:
                movie_data = movie_data['program']

                self.get_all_languages(movie_data)

                subs, lang_paths = self.get_subtitle(
                    movie_data, folder_path, file_name)
                subtitles += subs
                languages = set.union(languages, lang_paths)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)
        else:
            self.logger.error(res.text)

    def series_subtitle(self, data, mode_code, lang_code):
        title = data['name'].strip()
        album_id = data['albumId']
        start_order = data['from']

        episode_num = data['originalTotal']

        if 'maxOrder' in data:
            current_eps = data['maxOrder']
        else:
            current_eps = episode_num

        season_search = re.search(r'(.+)第(.+)季', title)
        if season_search:
            title = season_search.group(1).strip()
            season_name = cn2an(
                season_search.group(2))
        else:
            season_name = '01'

        season_index = int(season_name)

        self.logger.info("\n%s", title)

        episode_list = []

        page_size = math.ceil(current_eps / 24)
        for page in range(0, page_size):
            start_order = page * 24 + 1

            end_order = (page+1) * 24
            if end_order > current_eps:
                end_order = current_eps

            episode_list_url = self.api['episode_list'].format(
                album_id=album_id, mode_code=mode_code, lang_code=lang_code, end_order=current_eps, start_order=start_order)
            self.logger.debug("episode_list_url: %s", episode_list_url)
            res = self.session.get(url=episode_list_url)

            if res.ok:
                episode_list_data = res.json()
                self.logger.debug("episode_list: %s", episode_list_data)
                episode_list += episode_list_data['data']['epg']
            else:
                self.logger.error(res.text)

        if self.last_episode:
            episode_list = [list(episode_list)[-1]]
            self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                             int(season_name), current_eps, int(season_name))
        else:
            if current_eps == episode_num:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                 int(season_name),
                                 episode_num)
            else:
                self.logger.info(
                    self._(
                        "\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                    int(season_name),
                    episode_num,
                    current_eps)

        title = self.ripprocess.rename_file_name(
            f'{title}.S{str(season_index).zfill(2)}')

        folder_path = os.path.join(self.download_path, title)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        languages = set()
        subtitles = []

        for episode in episode_list:
            if 'payMarkFont' in episode and episode['payMarkFont'] == 'Preview':
                break
            if 'order' in episode:
                episode_index = int(episode['order'])
                if not self.download_season or season_index in self.download_season:
                    if not self.download_episode or episode_index in self.download_episode:
                        file_name = f'{title}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.IQIYI}.vtt'
                        self.logger.info(
                            self._("Finding %s ..."), file_name)

                        tvid = episode['qipuId']
                        play_url = f"https://www.iq.com/play/{episode['playLocSuffix']}"
                        vid = self.get_vid(play_url)
                        dash_url = self.get_dash_url(
                            vid=vid, tvid=tvid)
                        self.logger.debug("dash url: %s", dash_url)

                        episode_res = self.session.get(
                            url=dash_url)

                        if episode_res.ok:
                            episode_data = episode_res.json()[
                                'data']
                            if 'program' in episode_data:
                                episode_data = episode_data['program']

                                self.get_all_languages(
                                    episode_data)

                                subs, lang_paths = self.get_subtitle(
                                    episode_data, folder_path, file_name)
                                subtitles += subs
                                languages = set.union(
                                    languages, lang_paths)
                        else:
                            self.logger.error(episode_res.text)
                            sys.exit(1)

        self.download_subtitle(
            subtitles=subtitles, languages=languages, folder_path=folder_path)

    def get_auth_key(self, tvid):
        text = f"d41d8cd98f00b204e9800998ecf8427e{int(time() * 1000)}{tvid}"
        md = md5()
        md.update(text.encode())
        return md.hexdigest()

    def get_dash_url(self, vid, tvid):
        cookies = self.cookies.get_cookies()

        params = {
            "tvid": tvid,
            "bid": "",
            "vid": vid,
            "src": "01011021010010000000",
            "vt": "0",
            "rs": "1",
            "uid": cookies.get('P00003') if cookies.get('P00003') else '0',
            "ori": "pcw",
            "ps": "0",
            "k_uid": cookies['QC005'],
            "pt": "0",
            "d": "0",
            "s": "",
            "lid": "",
            "slid": "0",
            "cf": "",
            "ct": "",
            "authKey": self.get_auth_key(tvid),
            "k_tag": "1",
            "ost": "0",
            "ppt": "0",
            "dfp": cookies['__dfp'],
            "locale": "zh_cn",
            "prio": '{"ff":"","code":}',
            "k_err_retries": "0",
            "qd_v": "2",
            "tm": int(time() * 1000),
            "qdy": "a",
            "qds": "0",
            # "k_ft2": "8191",
            "k_ft1": "143486267424900",
            "k_ft4": "1581060",
            "k_ft7": "4",
            "k_ft5": "1",
            "bop": '{"version":"10.0","dfp":""}',
            "ut": "1",
        }
        url = "/dash?" + urlencode(params)
        cmdx5js = os.path.join(os.path.dirname(
            __file__).replace('\\', '/'), 'cmd5x.js')
        process = subprocess.run(f"node {cmdx5js} {quote(url)}",
                                 shell=True, stdout=subprocess.PIPE, check=False)
        vf = process.stdout.decode("utf-8")
        self.logger.debug("vf: %s", vf)
        return f"https://cache-video.iq.com{url}&vf={vf}"

    def get_subtitle(self, data, folder_path, file_name):

        lang_paths = set()
        subtitles = []
        for sub in data['stl']:
            self.logger.debug(sub)
            sub_lang = self.get_language_code(sub['_name'])
            if sub_lang in self.language_list:
                if len(self.language_list) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                if 'webvtt' in sub:
                    subtitle_link = sub['webvtt']
                    subtitle_file_name = file_name.replace(
                        '.vtt', f'.{sub_lang}.vtt')
                else:
                    subtitle_link = sub['xml']
                    subtitle_file_name = file_name.replace(
                        '.vtt', f'.{sub_lang}.xml')

                subtitle_link = self.api['meta'] + \
                    subtitle_link.replace('\\/', '/')

                os.makedirs(lang_folder_path,
                            exist_ok=True)

                subtitle = dict()
                subtitle['name'] = subtitle_file_name
                subtitle['path'] = lang_folder_path
                subtitle['url'] = subtitle_link
                subtitles.append(subtitle)
        return subtitles, lang_paths

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, lang=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.IQIYI, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)

    def main(self):
        self.get_language_list()
        self.cookies.load_cookies('__dfp')

        if 'play/' in self.url:
            content_id = re.search(
                r'https://www.iq.com/play/.+\-([^-]+)\?lang=.+', self.url)
            if not content_id:
                content_id = re.search(
                    r'https://www.iq.com/play/([^-]+)', self.url)
            self.url = f'https://www.iq.com/album/{content_id.group(1)}'

        res = self.session.get(url=self.url)
        if res.ok:
            match = re.search(r'({\"props\":{.*})', res.text)

            if not match:
                self.logger.error("Please input correct album url!")
                sys.exit(1)

            data = orjson.loads(match.group(1))['props']

            mode_code = data['initialProps']['pageProps']['modeCode']
            lang_code = data['initialProps']['pageProps']['langCode']

            data = data['initialState']['album']['videoAlbumInfo']

            allow_regions = data['regionsAllowed'].split(',')
            if not self.region.lower() in allow_regions:
                self.logger.info(
                    self._("\nThis video is only allows in:\n%s"), ', '.join(allow_regions))
                sys.exit(0)

            if data['videoType'] != 'singleVideo':
                self.series_subtitle(
                    data=data, mode_code=mode_code, lang_code=lang_code)
            else:
                self.movie_subtitle(data=data)
        else:
            self.logger.error(res.text)
