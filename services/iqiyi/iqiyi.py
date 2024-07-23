#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from iq.com
"""

from hashlib import md5
import math
import re
import os
import shutil
import subprocess
import sys
from time import sleep, time
from urllib.parse import urlencode
import orjson
from utils.helper import get_locale, get_language_code, get_all_languages
from utils.io import download_files, rename_filename
from utils.subtitle import convert_subtitle
from utils.proxy import get_ip_info
from services.baseservice import BaseService


class IQIYI(BaseService):
    """
    Service code for iQIYI streaming service (https://www.iq.com/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def get_vid(self, play_url):
        vid = ''
        sleep(2)
        res = self.session.get(play_url, timeout=5)
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

        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        filename = f'{title}.WEB-DL.{self.platform}.vtt'

        self.logger.info(self._(
            "\nDownload: %s\n---------------------------------------------------------------"), filename)

        play_url = f"https:{data['playUrl']}"
        vid = self.get_vid(play_url)
        tvid = data['qipuId']
        dash_url = self.get_dash_url(
            vid=vid, tvid=tvid)
        self.logger.debug("dash url: %s", dash_url)

        res = self.session.get(url=dash_url, timeout=5)
        if res.ok:
            movie_data = res.json()['data']
            languages = set()
            subtitles = []
            if 'program' in movie_data:
                movie_data = movie_data['program']
                subs, lang_paths = self.get_subtitle(
                    movie_data, folder_path, filename)
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

        title, season_index = self.get_title_and_season_index(title)
        self.logger.info("\n%s", title)

        episode_list = []

        page_size = math.ceil(current_eps / 24)
        for page in range(0, page_size):
            start_order = page * 24 + 1

            end_order = (page+1) * 24
            if end_order > current_eps:
                end_order = current_eps

            episode_list_url = self.config['api']['episode_list'].format(
                album_id=album_id, mode_code=mode_code, lang_code=lang_code, end_order=current_eps, start_order=start_order)
            self.logger.debug("episode_list_url: %s", episode_list_url)
            res = self.session.get(url=episode_list_url, timeout=5)

            if res.ok:
                episode_list_data = res.json()
                self.logger.debug("episode_list: %s", episode_list_data)
                episode_list += episode_list_data['data']['epg']
            else:
                self.logger.error(res.text)

        if self.last_episode:
            episode_list = [list(episode_list)[-1]]
            self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                             season_index, current_eps, season_index)
        else:
            if current_eps == episode_num:
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                 season_index,
                                 episode_num)
            else:
                self.logger.info(
                    self._(
                        "\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                    season_index,
                    episode_num,
                    current_eps)

        name = rename_filename(
            f'{title}.S{str(season_index).zfill(2)}')

        folder_path = os.path.join(self.download_path, name)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        languages = set()
        subtitles = []
        for episode in episode_list:
            if 'episodeType' in episode:
                if 'episodeType' in episode:
                    if episode['episodeType'] == 1 or episode['episodeType'] == 6:
                        continue
            if 'order' in episode:
                episode_index = int(episode['order'])
                if episode_index == -1:
                    episode_index = 0
                if not self.download_season or season_index in self.download_season:
                    if not self.download_episode or episode_index in self.download_episode:
                        filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'
                        self.logger.info(
                            self._("Finding %s ..."), filename)

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

                                subs, lang_paths = self.get_subtitle(
                                    episode_data, folder_path, filename)
                                subtitles += subs
                                languages = set.union(
                                    languages, lang_paths)
                            elif 'boss_ts' in episode_data:
                                self.logger.error(
                                    episode_data['boss_ts']['msg'])
                            else:
                                self.logger.error(
                                    "Invaild dash_url, wrong vf!")
                                self.logger.error(
                                    "Renew your cookies and try again!")
                                sys.exit(1)
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
        """Get vf and return dash url"""

        params = {
            "tvid": tvid,
            "bid": "",
            "vid": vid,
            "src": "01011021010010000000",
            "vt": "0",
            "rs": "1",
            "uid": self.cookies.get('P00003') if self.cookies.get('P00003') else '0',
            "ori": "pcw",
            "ps": "0",
            "k_uid": self.cookies['QC005'],
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
            "dfp": self.cookies['__dfp'],
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

        executable = shutil.which('node')
        if not executable:
            raise EnvironmentError("Nodejs not found...")
        process = subprocess.run(
            [executable, cmdx5js, url], stdout=subprocess.PIPE, check=False)
        vf = process.stdout.decode("utf-8").strip()
        self.logger.debug("vf: %s", vf)
        return f"https://cache-video.iq.com{url}&vf={vf}"

    def get_subtitle(self, data, folder_path, filename):

        lang_paths = set()
        subtitles = []

        if 'stl' in data:
            available_languages = set()
            for sub in data['stl']:
                self.logger.debug('sub: %s', sub)
                sub_lang = get_language_code(sub['_name'])
                available_languages.add(sub_lang)
                if sub_lang in self.subtitle_language or 'all' in self.subtitle_language:
                    if len(self.subtitle_language) > 1 or 'all' in self.subtitle_language:
                        lang_folder_path = os.path.join(folder_path, sub_lang)
                    else:
                        lang_folder_path = folder_path
                    lang_paths.add(lang_folder_path)

                    if 'webvtt' in sub:
                        subtitle_link = sub['webvtt']
                        subtitle_filename = filename.replace(
                            '.vtt', f'.{sub_lang}.vtt')
                    else:
                        subtitle_link = sub['xml']
                        subtitle_filename = filename.replace(
                            '.vtt', f'.{sub_lang}.xml')

                    subtitle_link = self.config['api']['meta'] + \
                        subtitle_link.replace('\\/', '/')

                    os.makedirs(lang_folder_path,
                                exist_ok=True)

                    subtitle = dict()
                    subtitle['name'] = subtitle_filename
                    subtitle['path'] = lang_folder_path
                    subtitle['url'] = subtitle_link
                    subtitles.append(subtitle)

            get_all_languages(available_languages=available_languages,
                              subtitle_language=self.subtitle_language, locale_=self.locale)
        else:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
        return subtitles, lang_paths

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
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
            self.GEOFENCE = allow_regions
            if not get_ip_info()['country'].lower() in allow_regions:
                self.set_proxy(allow_regions[0])
                if not get_ip_info(self.session)['country'].lower() in allow_regions:
                    self.logger.error(
                        self._("\nThis video is only allows in:\n%s"), ', '.join(allow_regions))
                    sys.exit(1)
            if data['videoType'] != 'singleVideo':
                self.series_subtitle(
                    data=data, mode_code=mode_code, lang_code=lang_code)
            else:
                self.movie_subtitle(data=data)
        else:
            self.logger.error(res.text)
