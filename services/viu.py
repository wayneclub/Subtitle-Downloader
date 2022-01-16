#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from Disney+
"""

import re
import os
import logging
import shutil
import orjson
from common.utils import Platform, get_locale, get_user_agent, http_request, HTTPMethod, download_files
from common.subtitle import convert_subtitle, merge_subtitle_fragments
from services.service import Service


class Viu(Service):

    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.subtitle_language = args.subtitle_language
        self.language_list = []

        self.token = ""

        self.api = {
            'ott': 'https://www.viu.com/ott/{region}/index.php?area_id={area_id}&language_flag_id={language_flag_id}&r=vod/ajax-detail&platform_flag_label=web&area_id={area_id}&language_flag_id={language_flag_id}&product_id={product_id}',
            'load': 'https://viu.com/ott/web/api/container/load?ver=1.0&fmt=json&aver=5.0&appver=2.0&appid=viu_desktop&platform=desktop&id=playlist-{playlist_id}&start=0&limit=20&filter=mixed&contentCountry={region}&contentFlavour=all&regionid=all&languageid=en&ccode={region}&geo={geo}&iid=41be67db-a75a-4525-9d25-f41034cc578c',
            'token': 'https://um.viuapi.io/user/identity?ver=1.0&fmt=json&aver=5.0&appver=2.0&appid=viu_desktop&platform=desktop&iid=c1757177-ad9e-4cbb-8025-7f11569645d6'
        }

    def get_language_code(self, lang):
        language_code = {
            'en': 'en',
            'zh': 'zh-Hans',
            'zh-CN': 'zh-Hans',
            'zh-Hant': 'zh-Hant',
            'ms': 'ms',
            'th': 'th',
            'id': 'id',
            'my': 'my',
            'mya': 'mya'
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

    def get_all_languages(self, available_languages):

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error(
                self._("\nSubtitle available languages: %s"), available_languages)
            exit(0)

    def get_region(self):
        region = ''
        area_id = ''
        language_flag_id = ''
        region_search = re.search(r'\/ott\/(.+?)\/(.+?)\/', self.url)
        if region_search:
            region = region_search.group(1)
            language = region_search.group(2)
            if region == 'sg':
                area_id = 2
                language_flag_id = ''
                if 'zh' in language:
                    language_flag_id = '2'
                else:
                    language_flag_id = '3'
            else:
                region = 'hk'
                area_id = 1
                if 'zh' in language:
                    language_flag_id = '1'
                else:
                    language_flag_id = '3'
        return region, area_id, language_flag_id

    def get_token(self):
        headers = {
            'accept': 'application/json; charset=utf-8',
            'content-type': 'application/json; charset=UTF-8',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': get_user_agent(),
            'Origin': 'https://viu.com',
            'x-session-id': 'ac20455d-5263-45ed-8b07-3e8a215af8fd',
            'x-client': 'browser'
        }
        postdata = {'deviceId': '18b79bc4-73b0-481a-8045-38d4cbc83b07'}
        kwargs = {'json': postdata}
        data = http_request(
            session=self.session, url=self.api['token'], method=HTTPMethod.POST, headers=headers, kwargs=kwargs)
        self.token = data['token']


    def download_subtitle(self):
        product_id_search = re.search(r'vod\/(\d+)\/', self.url)
        if product_id_search:
            product_id = product_id_search.group(1)
            response = http_request(
                session=self.session, url=self.url, method=HTTPMethod.GET, raw=True)
            match = re.search(
                r'href=\"\/ott\/(.+)\/index\.php\?r=campaign\/connectwithus\&language_flag_id=(\d+)\&area_id=(\d+)\"', response)
            if match:
                region = match.group(1)
                language_flag_id = match.group(2)
                area_id = match.group(3)
            else:
                region, area_id, language_flag_id = self.get_region()
            self.logger.debug(
                "region: %s, area_id: %s, language_flag_id: %s", region, area_id, language_flag_id)

            meta_url = self.api['ott'].format(
                region=region, area_id=area_id, language_flag_id=language_flag_id, product_id=product_id)
            self.logger.debug(meta_url)
            data = http_request(
                session=self.session, url=meta_url, method=HTTPMethod.GET)['data']
            self.logger.debug(data)

            title = data['series']['name']
            if data['series']['name'].split(' ')[-1].isdecimal():
                title = title.replace(
                    data['series']['name'].split(' ')[-1], '').strip()
                season_name = data['series']['name'].split(' ')[-1].zfill(2)
            else:
                season_name = '01'

            self.logger.info(self._("\n%s Season %s"),
                            title, int(season_name))

            folder_path = os.path.join(
                self.output, f'{title}.S{season_name}')

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            episode_num = data['series']['product_total']
            current_eps = data['current_product']['released_product_total']

            episode_list = reversed(data['series']['product'])

            if self.last_episode:
                episode_list = [list(episode_list)[-1]]
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                int(season_name), current_eps, int(season_name))
            else:
                if current_eps != episode_num:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                    int(season_name), episode_num, current_eps)
                else:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                    int(season_name), episode_num)

            languages = set()
            subtitles = []
            for episode in episode_list:
                episode_name = str(episode['number']).zfill(2)

                episode_url = re.sub(r'(.+product_id=).+', '\\1',
                                    meta_url) + episode['product_id']

                file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.{Platform.VIU}.vtt'

                self.logger.info(self._("Finding %s ..."), file_name)
                episode_data = http_request(session=self.session,
                                            url=episode_url, method=HTTPMethod.GET)['data']['current_product']['subtitle']

                available_languages = tuple([self.get_language_code(sub['code']) for sub in episode_data])
                self.get_all_languages(available_languages)

                subs, lang_paths = self.get_subtitle(
                    episode_data, folder_path, file_name)
                subtitles += subs
                languages = set.union(languages, lang_paths)

            download_files(subtitles)

            display = True
            for lang_path in sorted(languages):
                if 'tmp' in lang_path:
                    merge_subtitle_fragments(
                        folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                    display = False
                convert_subtitle(folder_path=lang_path, lang=self.locale)

            convert_subtitle(folder_path=folder_path,
                            platform=Platform.VIU, lang=self.locale)
        else:
            playlist_id_search = re.search(r'.+playlist-(\d+)', self.url)
            if playlist_id_search:
                playlist_id = playlist_id_search.group(1)
                self.get_token()
                response = http_request(
                session=self.session, url=self.url, method=HTTPMethod.GET, raw=True)
                match = re.search(r'window\.__INITIAL_STATE__=(\{.+?\});', response)
                if match:
                    geo_data = orjson.loads(match.group(1))
                    region = geo_data['config']['location']['countryCode']
                    geo = geo_data['config']['location']['geo']
                else:
                    region = 'ID'
                    geo = '10'
                meta_url = self.api['load'].format(
                region=region, geo=geo, playlist_id=playlist_id)
                self.logger.debug(meta_url)
                headers = {
                    'accept': 'application/json; charset=utf-8',
                    'authorization': f'Bearer {self.token}',
                    'content-type': 'application/json; charset=UTF-8',
                    'Sec-Fetch-Mode': 'cors',
                    'User-Agent': get_user_agent()
                }
                self.logger.debug(meta_url)
                data = http_request(
                    session=self.session, url=meta_url, method=HTTPMethod.GET, headers=headers)
                self.logger.debug(data)
                data = data['response']['container']
                self.logger.debug(data)
                title = data['title']
                if data['title'].split(' ')[-1].isdecimal():
                    title = title.replace(
                        data['title'].split(' ')[-1], '').strip()
                    season_name = data['title'].split(' ')[-1].zfill(2)
                else:
                    season_name = '01'

                self.logger.info(self._("\n%s Season %s"),
                        title, int(season_name))

                folder_path = os.path.join(
                    self.output, f'{title}.S{season_name}')

                episode_list = [ep for ep in data['item'] if 'slug' in ep and 'trailer' not in ep['slug'] and 'teaser' not in ep['slug']]

                episode_num = len(episode_list)
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                int(season_name), episode_num)

                languages = set()
                subtitles = []
                for episode in episode_list:
                    episode_name = str(episode['episodeno']).zfill(2)

                    file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.{Platform.VIU}.vtt'


                    self.logger.info(self._("Finding %s ..."), file_name)

                    subtitle_data = episode['media']['subtitles']['subtitle']
                    available_languages = set([self.get_language_code(sub['language']) for sub in subtitle_data])
                    self.get_all_languages(available_languages)

                    url_path = episode['urlpath']

                    subs, lang_paths = self.get_subtitle_2(subtitle_data, url_path, folder_path, file_name)
                    subtitles += subs
                    languages = set.union(languages, lang_paths)

                self.logger.debug('subtitles: %s', subtitles)
                download_files(subtitles)
                display = True
                for lang_path in sorted(languages):
                    if 'tmp' in lang_path:
                        merge_subtitle_fragments(
                            folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                        display = False
                    convert_subtitle(folder_path=lang_path, lang=self.locale)

                convert_subtitle(folder_path=folder_path,
                                platform=Platform.VIU, lang=self.locale)




    def get_subtitle(self, data, folder_path, file_name):

        lang_paths = set()

        subtitles = []
        for sub in data:
            self.logger.debug(sub['code'])
            sub_lang = self.get_language_code(sub['code'])
            if sub_lang in self.language_list:
                subtitle = dict()
                if len(self.language_list) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path

                subtitle_file_name = file_name.replace(
                    '.vtt', f'.{sub_lang}.vtt')

                subtitle['url'] = sub['subtitle_url'].replace('\\/', '/')

                subtitle['segment'] = False

                if 'second_subtitle_url' in sub and sub['second_subtitle_url']:
                    lang_folder_path = os.path.join(
                        lang_folder_path, f"tmp_{subtitle_file_name.replace('.vtt', '.srt')}")
                    subtitle['segment'] = True

                subtitle['name'] = subtitle_file_name

                subtitle['path'] = lang_folder_path

                subtitles.append(subtitle)

                if 'second_subtitle_url' in sub and sub['second_subtitle_url']:
                    second_subtitle = dict()
                    second_subtitle['segment'] = True
                    second_subtitle['url'] = sub['second_subtitle_url'].replace(
                        '\\/', '/')
                    second_subtitle['name'] = subtitle_file_name
                    second_subtitle['path'] = lang_folder_path
                    subtitles.append(second_subtitle)

                lang_paths.add(lang_folder_path)
                os.makedirs(lang_folder_path,
                            exist_ok=True)

        return subtitles, lang_paths

    def get_subtitle_2(self, data, url_path, folder_path, file_name):

        lang_paths = set()

        subtitles = []
        for sub in data:
            self.logger.debug(sub['language'])
            sub_lang = self.get_language_code(sub['language'])
            if sub_lang in self.language_list and sub['format'] == 'vtt':
                subtitle = dict()
                if len(self.language_list) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path

                subtitle_file_name = file_name.replace(
                    '.vtt', f'.{sub_lang}.vtt')

                subtitle['url'] = url_path + '/' + sub['language'] + '.vtt'
                self.logger.info(subtitle['url'])

                subtitle['segment'] = False

                subtitle['name'] = subtitle_file_name

                subtitle['path'] = lang_folder_path

                subtitles.append(subtitle)

                lang_paths.add(lang_folder_path)
                os.makedirs(lang_folder_path,
                            exist_ok=True)

        return subtitles, lang_paths

    def main(self):
        self.get_language_list()
        self.download_subtitle()
