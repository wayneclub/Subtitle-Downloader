#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from iQIYI
"""

import re
import os
import shutil
import logging
import orjson
from common.utils import get_locale, Platform, http_request, HTTPMethod, get_ip_location, driver_init, get_network_url, download_files
from common.subtitle import convert_subtitle
from common.dictionary import convert_chinese_number
from services.service import Service


class IQIYI(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)
        self.subtitle_language = args.subtitle_language

        self.language_list = ()

        self.api = {
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
            '西班牙語': 'es'
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
            self.logger.info(
                self._("\nSorry, there's no embeded subtitles in this video!"))
            exit(0)

        available_languages = tuple(
            [self.get_language_code(sub['_name']) for sub in data['stl']])

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            exit(0)

    def download_subtitle(self):
        response = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)
        match = re.search(r'({\"props\":{.*})', response)
        data = orjson.loads(match.group(1))
        drama = data['props']['initialState']

        if drama and 'album' in drama:
            info = drama['album']['videoAlbumInfo']
            if info:
                title = info['name'].strip()
                episode_num = info['originalTotal']
                allow_regions = info['regionsAllowed'].split(',')
                if not get_ip_location()['country'].lower() in allow_regions:
                    self.logger.info(
                        self._("\nThis video is only allows in:\n%s"), ', '.join(allow_regions))
                    exit(0)

                if 'maxOrder' in info:
                    current_eps = info['maxOrder']
                else:
                    current_eps = episode_num

                season_search = re.search(r'(.+)第(.+)季', title)
                if season_search:
                    title = season_search.group(1).strip()
                    season_name = convert_chinese_number(
                        season_search.group(2))
                else:
                    season_name = '01'

                self.logger.info("\n%s", title)

            episode_list = []
            if 'cacheAlbumList' in drama['album'] and '1' in drama['album']['cacheAlbumList'] and len(drama['album']['cacheAlbumList']['1']) > 0:
                episode_list = drama['album']['cacheAlbumList']['1']
            elif 'play' in drama and 'cachePlayList' in drama['play'] and '1' in drama['play']['cachePlayList'] and len(drama['play']['cachePlayList']['1']) > 0:
                episode_list = drama['play']['cachePlayList']['1']

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

            folder_path = os.path.join(self.output, f'{title}.S{season_name}')
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            languages = set()
            subtitles = []
            if len(episode_list) > 0:
                driver = driver_init()
                lang_paths = set()
                for episode in episode_list:
                    if 'payMarkFont' in episode and episode['payMarkFont'] == 'Preview':
                        break
                    if 'order' in episode:
                        episode_name = str(episode['order']).zfill(2)
                    if 'albumPlayUrl' in episode:
                        episode_url = re.sub(
                            '^//', 'https://', episode['albumPlayUrl']).replace('lang=en_us', 'lang=zh_tw').replace('lang=zh_cn', 'lang=zh_tw').strip()
                        self.logger.debug(episode_url)
                        driver.get(episode_url)

                        file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.{Platform.IQIYI}.vtt'

                        self.logger.info(self._("Finding %s ..."), file_name)
                        dash_url = get_network_url(
                            driver=driver, search_url=r"https:\/\/cache-video.iq.com\/dash\?", lang=self.locale)
                        self.logger.debug(dash_url)

                        episode_data = http_request(session=self.session,
                                                    url=dash_url, method=HTTPMethod.GET)['data']
                        if 'program' in episode_data:
                            episode_data = episode_data['program']

                            self.get_all_languages(episode_data)

                            subs, lang_paths = self.get_subtitle(
                                episode_data, folder_path, file_name)
                            subtitles += subs
                            languages = set.union(languages, lang_paths)

                driver.quit()

                download_files(subtitles)

                for lang_path in sorted(languages):
                    convert_subtitle(folder_path=lang_path, lang=self.locale)
                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.IQIYI, lang=self.locale)

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

    def main(self):
        self.get_language_list()
        self.download_subtitle()
