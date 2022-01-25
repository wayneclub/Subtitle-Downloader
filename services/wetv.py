#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Friday影音
"""

import logging
import os
from platform import release
import re
import shutil
import orjson
from bs4 import BeautifulSoup
from common.utils import get_locale, Platform, http_request, HTTPMethod, driver_init, get_network_url, download_files, save_html
from common.subtitle import convert_subtitle
from common.dictionary import convert_chinese_number
from services.service import Service


class WeTV(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)
        self.subtitle_language = args.subtitle_language

        self.language_list = ()

        self.api = {
            'play': 'https://wetv.vip/id/play/{series_id}/{episode_id}',
        }

    def get_language_code(self, lang):
        language_code = {
            'EN': 'en',
            'ZH-TW': 'zh-Hant',
            'ZH-CN': 'zh-Hans',
            'MS': 'ms',
            'TH': 'th',
            'ID': 'id',
            'PT': 'pt',
            'ES': 'es',
            'KO': 'ko',
            'VI': 'vi',
            'AR': 'ar',
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def get_all_languages(self, data):

        if not 'fi' in data:
            self.logger.info(
                self._("\nSorry, there's no embeded subtitles in this video!"))
            exit(0)

        available_languages = tuple(
            [self.get_language_code(sub['lang']) for sub in data['fi']])

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            exit(0)

    def movie_subtitle(self, data):
        title = data['videoInfo']['title']
        self.logger.info("\n%s", title)

        release_year = data['videoInfo']['publish_date'][:4]

        folder_path = os.path.join(
            self.output, f'{title}.{release_year}')
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.{release_year}.WEB-DL.{Platform.WETV}.vtt'
        self.logger.info(
            self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

        movie_url = self.api['play'].format(
            series_id=data['videoInfo']['cover_list'][0], episode_id=data['videoInfo']['vid'])
        driver = driver_init()

        driver.get(movie_url)

        getvinfo_url = get_network_url(
            driver=driver, search_url=r"https:\/\/play.wetv.vip\/getvinfo\?", lang=self.locale)
        self.logger.debug(getvinfo_url)

        movie_data = http_request(session=self.session,
                                  url=getvinfo_url, method=HTTPMethod.GET, raw=True)
        movie_data = orjson.loads(
            re.sub(r'txplayerJsonpCallBack_getinfo_\d+\(({.+})\)', '\\1', movie_data))

        driver.quit()

        languages = set()
        subtitles = []
        if 'sfl' in movie_data:
            movie_data = movie_data['sfl']
            self.logger.debug(movie_data)
            self.get_all_languages(movie_data)

            subs, lang_paths = self.get_subtitle(
                movie_data, folder_path, file_name)
            subtitles += subs
            languages = set.union(
                languages, lang_paths)

            if subtitles and languages:
                download_files(subtitles)

                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, lang=self.locale)
                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.WETV, lang=self.locale)

    def series_subtitle(self, data):
        title = data['coverInfo']['title']
        season_search = re.search(r'(.+)第(.+)季', title)
        if season_search:
            title = season_search.group(1).strip()
            season_name = convert_chinese_number(
                season_search.group(2))
        else:
            season_name = '01'

        self.logger.info("\n%s", title)

        series_id = data['coverInfo']['cover_id']
        current_eps = data['coverInfo']['episode_updated_country']
        episode_num = data['coverInfo']['episode_all']

        episode_list = data['videoList']

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

        folder_path = os.path.join(
            self.output, f'{title}.S{season_name}')
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        if len(episode_list) > 0:
            driver = driver_init()
            languages = set()
            subtitles = []
            for episode in episode_list:
                episode_name = episode['episode']
                episode_id = episode['vid']
                episode_url = self.api['play'].format(
                    series_id=series_id, episode_id=episode_id)
                self.logger.debug(episode_url)

                file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.{Platform.WETV}.vtt'
                self.logger.info(
                    self._("Finding %s ..."), file_name)

                driver.get(episode_url)

                getvinfo_url = get_network_url(
                    driver=driver, search_url=r"https:\/\/play.wetv.vip\/getvinfo\?", lang=self.locale)
                self.logger.debug(getvinfo_url)
                episode_data = http_request(session=self.session,
                                            url=getvinfo_url, method=HTTPMethod.GET, raw=True)
                episode_data = orjson.loads(
                    re.sub(r'txplayerJsonpCallBack_getinfo_\d+\(({.+})\)', '\\1', episode_data))

                if 'sfl' in episode_data:
                    episode_data = episode_data['sfl']
                    self.logger.debug(episode_data)
                    self.get_all_languages(episode_data)

                    subs, lang_paths = self.get_subtitle(
                        episode_data, folder_path, file_name)
                    subtitles += subs
                    languages = set.union(
                        languages, lang_paths)

            driver.quit()
            if subtitles and languages:
                download_files(subtitles)

                for lang_path in sorted(languages):
                    convert_subtitle(
                        folder_path=lang_path, lang=self.locale)
                convert_subtitle(folder_path=folder_path,
                                 platform=Platform.WETV, lang=self.locale)

    def get_subtitle(self, data, folder_path, file_name):

        lang_paths = set()
        subtitles = []
        for sub in data['fi']:
            self.logger.debug(sub)
            sub_lang = self.get_language_code(sub['lang'])
            if sub_lang in self.language_list:
                if len(self.language_list) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                subtitle_link = sub['url']
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

    def download_subtitle(self):
        """Download subtitle from WeTV"""

        response = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)
        match = re.search(
            r'<script id=\"__NEXT_DATA__" type=\"application/json\">(.+?)<\/script>', response)
        if match:
            data = orjson.loads(match.group(1).strip())[
                'props']['pageProps']['data']
            data = orjson.loads(data)

            if data['coverInfo']['is_area_limit'] == 1:
                self.logger.info(
                    self._("\nSorry, this video is not allow in your region!"))
                exit(0)

            if data['coverInfo']['type'] == 1:
                self.movie_subtitle(data)
            else:
                self.series_subtitle(data)

    def main(self):
        self.get_language_list()
        self.download_subtitle()
