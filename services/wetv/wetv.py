#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from WeTV
"""

import os
from random import randint
import re
import shutil
import sys
from urllib.parse import urljoin
import m3u8
import orjson
from time import time
from cn2an import cn2an
from configs.config import user_agent
from utils.io import rename_filename, download_files
from utils.helper import get_locale, get_language_code
from utils.subtitle import convert_subtitle
from services.service import Service
from services.wetv.ckey import CKey


class WeTV(Service):
    """
    Service code for WeTV streaming service (https://wetv.vip/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def get_all_languages(self, data):
        """Get all subtitles language"""

        if not 'fi' in data:
            self.logger.error(
                self._("\nSorry, there's no embedded subtitles in this video!"))
            sys.exit(0)

        available_languages = tuple(
            [get_language_code(sub['lang']) for sub in data['fi']])

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
        title = data['videoInfo']['title']
        release_year = data['videoInfo']['videoCheckUpTime'][:4]
        self.logger.info("\n%s (%s)", title, release_year)

        title = rename_filename(f'{title}.{release_year}')

        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{self.platform}.vtt'
        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

        movie_data = self.get_dash_url(
            cid=data['videoInfo']['coverList'][0], vid=data['videoInfo']['vid'], url=self.url)

        languages = set()
        subtitles = []

        if movie_data:
            subs, lang_paths = self.get_subtitle(
                movie_data, folder_path, file_name)
            subtitles += subs
            languages = set.union(
                languages, lang_paths)

        self.download_subtitle(
            subtitles=subtitles, languages=languages, folder_path=folder_path)

    def series_subtitle(self, data):
        title = data['coverInfo']['title']

        season_search = re.search(r'(.+)第(.+)季', title)
        season_search_eng = re.search(r'(.+) S(\d+)', title)
        if season_search:
            title = season_search.group(1).strip()
            season_name = cn2an(
                season_search.group(2))
        elif season_search_eng:
            title = season_search_eng.group(1).strip()
            season_name = season_search_eng.group(2).strip()
        else:
            season_name = '01'

        season_index = int(season_name)

        self.logger.info("\n%s", title)

        series_id = data['coverInfo']['cid']
        current_eps = data['coverInfo']['episodeUpdated']
        episode_num = data['coverInfo']['episodeAll']

        episode_list = data['videoList']

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

        if len(episode_list) > 0:
            languages = set()
            subtitles = []
            for episode in episode_list:
                if episode['isTrailer'] == 1:
                    continue
                episode_index = int(episode['episode'])
                if not self.download_season or season_index in self.download_season:
                    if not self.download_episode or episode_index in self.download_episode:
                        episode_id = episode['vid']
                        episode_url = self.config['api']['play'].format(
                            series_id=series_id, episode_id=episode_id)
                        self.logger.debug(episode_url)

                        file_name = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.vtt'
                        self.logger.info(
                            self._("Finding %s ..."), file_name)

                        episode_data = self.get_dash_url(
                            cid=series_id, vid=episode_id, url=self.url)

                        if episode_data:
                            subs, lang_paths = self.get_subtitle(
                                episode_data, folder_path, file_name)
                            subtitles += subs
                            languages = set.union(
                                languages, lang_paths)

            self.download_subtitle(
                subtitles=subtitles, languages=languages, folder_path=folder_path)

    def get_dash_url(self, cid, vid, url):
        guid = self.cookies['guid']
        tm = str(int(time()))
        ckey = CKey().make(vid=vid, tm=tm, app_ver='2.5.13',
                           guid=guid, platform='4830201', url=url)

        headers = {
            'Referer': url,
            'User-Agent': user_agent
        }

        params = {
            'charge': '0',
            'otype': 'json',
            'defnpayver': '0',
            'spau': '1',
            'spaudio': '1',
            'spwm': '1',
            'sphls': '1',
            'host': 'wetv.vip',
            'refer': 'wetv.vip',
            'ehost': url,
            'sphttps': '1',
            'encryptVer': '8.1',
            'cKey': ckey,
            'clip': '4',
            'guid': guid,
            'flowid': '4bc874cf11eac741b34fa6e4c62ca18e',
            'platform': '4830201',
            'sdtfrom': '1002',
            'appVer': '2.5.13',
            'unid': '',
            'auth_from': '',
            'auth_ext': '',
            'vid': vid,
            'defn': 'shd',
            'fhdswitch': '0',
            'dtype': '3',
            'spsrt': '2',
            'tm': tm,
            'lang_code': '8229847',
            'logintoken': '',
            'spcaptiontype': '1',
            'spmasterm3u8': '2',
            'country_code': '153514',
            'cid': cid,
            'drm': '40',
            'callback': f'getinfo_callback_{randint(10000, 999999)}',
        }

        res = self.session.get(
            self.config['api']['getvinfo'], params=params, headers=headers, timeout=5)

        if res.ok:
            callback = re.sub(
                r'.+?\(({.+})\)', '\\1', res.text)
            if callback:
                data = orjson.loads(callback)
                if 'sfl' in data:
                    data = data['sfl']
                    self.logger.debug(data)
                    self.get_all_languages(data)
                    return data
                elif data['msg'] and data['msg'] == 'pay limit':
                    self.logger.warning("pay limit")
                else:
                    self.logger.error(res.text)
                    sys.exit(1)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def get_subtitle(self, data, folder_path, file_name):

        lang_paths = set()
        subtitles = []
        for sub in data['fi']:
            self.logger.debug(sub)
            sub_lang = get_language_code(sub['lang'])
            if sub_lang in self.subtitle_language:
                if len(self.subtitle_language) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                subtitle_link = sub['url']
                if '.m3u8' in subtitle_link:
                    subtitle_link = self.parse_m3u(subtitle_link)
                subtitle_file_name = file_name.replace(
                    '.vtt', f'.{sub_lang}.vtt')

                os.makedirs(lang_folder_path,
                            exist_ok=True)

                subtitle = dict()
                subtitle['name'] = subtitle_file_name
                subtitle['path'] = lang_folder_path
                subtitle['url'] = subtitle_link
                subtitles.append(subtitle)
        return subtitles, lang_paths

    def parse_m3u(self, m3u_link):
        segments = m3u8.load(m3u_link)
        return urljoin(segments.base_uri, segments.files[0])

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            download_files(subtitles)
            for lang_path in sorted(languages):
                convert_subtitle(
                    folder_path=lang_path, subtitle_format=self.subtitle_format, locale=self.locale)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
        """Download subtitle from WeTV"""

        res = self.session.get(url=self.url, timeout=5)
        if res.ok:
            match = re.search(
                r'<script id=\"__NEXT_DATA__" type=\"application/json\">(.+?)<\/script>', res.text)
            if match:
                data = orjson.loads(match.group(1).strip())[
                    'props']['pageProps']['data']
                data = orjson.loads(data)

                if data['coverInfo']['isAreaLimit'] == 1:
                    self.logger.info(
                        self._("\nSorry, this video is not allow in your region!"))
                    sys.exit(0)

                if data['coverInfo']['type'] == 1:
                    self.movie_subtitle(data)
                else:
                    self.series_subtitle(data)
        else:
            self.logger.error(res.text)
