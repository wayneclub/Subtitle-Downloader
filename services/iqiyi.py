"""
This module is to download subtitle from iQIYI
"""

import re
import os
import shutil
import logging
import orjson
import requests
from common.utils import http_request, HTTPMethod, get_ip_location, driver_init, get_network_url, convert_subtitle, download_file_multithread
from common.dictionary import convert_chinese_number


class IQIYI(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url.strip()

        if args.output:
            self.output = args.output.strip()
        else:
            self.output = os.getcwd()

        if args.season:
            self.download_season = int(args.season)
        else:
            self.download_season = None

        self.last_episode = args.last_episode

        self.subtitle_language = args.subtitle_language

        self.language_list = ()

        self.session = requests.Session()

        self.api = {
            'meta': 'https://meta.video.iqiyi.com'
        }

    def get_language_code(self, lang):
        language_code = {
            '英語': 'en',
            '繁體中文': 'zh-Hant',
            '簡體中文': 'zh-Hans',
            '馬來語': 'ms',
            '越南語': 'vi',
            '泰語': 'th',
            '印尼語': 'id',
            '阿拉伯語': 'ar'
        }

        if language_code.get(lang):
            return language_code.get(lang)

    def get_language_list(self):
        if not self.subtitle_language:
            self.subtitle_language = 'zh-Hant'

        self.language_list = tuple([
            language for language in self.subtitle_language.split(',')])

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
                        '你所在的地區無法下載，可用VPN換區到以下地區試看看：\n%s', ', '.join(allow_regions))
                    exit()

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

                self.logger.info('\n%s', title)

                if current_eps == episode_num:
                    self.logger.info('\n第 %s 季 共有：%s 集\t下載全集\n---------------------------------------------------------------',
                                     int(season_name),
                                     episode_num)
                else:
                    self.logger.info(
                        '\n第 %s 季 共有：%s 集\t更新至 第 %s 集\t下載全集\n---------------------------------------------------------------',
                        int(season_name),
                        episode_num,
                        current_eps)

            episode_list = []
            if 'cacheAlbumList' in drama['album'] and '1' in drama['album']['cacheAlbumList'] and len(drama['album']['cacheAlbumList']['1']) > 0:
                episode_list = drama['album']['cacheAlbumList']['1']
            elif 'play' in drama and 'cachePlayList' in drama['play'] and '1' in drama['play']['cachePlayList'] and len(drama['play']['cachePlayList']['1']) > 0:
                episode_list = drama['play']['cachePlayList']['1']

            folder_path = os.path.join(self.output, f'{title}.S{season_name}')
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

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

                        dash_url = get_network_url(
                            driver, r'https:\/\/cache-video.iq.com\/dash\?')
                        self.logger.debug(dash_url)

                        file_name = f'{title}.S{season_name}E{episode_name}.WEB-DL.iQiyi.srt'

                        lang_paths = self.get_subtitle(
                            dash_url, folder_path, file_name)

                driver.quit()

                for lang_path in lang_paths:
                    convert_subtitle(lang_path)
                convert_subtitle(folder_path, 'iqiyi')

    def get_subtitle(self, url, folder_path, file_name):
        response = http_request(session=self.session,
                                url=url, method=HTTPMethod.GET)

        data = response['data']['program']

        if not 'stl' in data:
            self.logger.info('抱歉，此劇只有硬字幕，可去其他串流平台查看')
            exit(0)
        else:
            data = data['stl']

        lang_paths = set()

        available_languages = tuple([self.get_language_code(
            sub['_name']) for sub in data])

        if 'all' in self.language_list:
            self.language_list = available_languages

        if not set(self.language_list).intersection(set(available_languages)):
            self.logger.error('提供的字幕語言：%s', available_languages)
            exit()

        subtitle_urls = []
        subtitle_names = []
        for sub in data:
            self.logger.debug(sub)
            sub_lang = self.get_language_code(sub['_name'])
            if sub_lang in self.language_list:
                if len(self.language_list) > 1:
                    lang_folder_path = os.path.join(folder_path, sub_lang)
                else:
                    lang_folder_path = folder_path
                lang_paths.add(lang_folder_path)

                if 'srt' in sub:
                    subtitle_link = sub['srt']
                    subtitle_file_name = file_name.replace(
                        '.srt', f'.{sub_lang}.srt')
                elif 'webvtt' in sub:
                    subtitle_link = sub['webvtt']
                    subtitle_file_name = file_name.replace(
                        '.srt', f'.{sub_lang}.vtt')
                else:
                    subtitle_link = sub['xml']
                    subtitle_file_name = file_name.replace(
                        '.srt', f'.{sub_lang}.xml')

                subtitle_link = self.api['meta'] + \
                    subtitle_link.replace('\\/', '/')

                os.makedirs(lang_folder_path,
                            exist_ok=True)
                subtitle_urls.append(subtitle_link)
                subtitle_names.append(os.path.join(
                    lang_folder_path, subtitle_file_name))

        download_file_multithread(subtitle_urls, subtitle_names)
        return lang_paths

    def main(self):
        self.get_language_list()
        self.download_subtitle()
