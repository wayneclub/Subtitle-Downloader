#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from iTunes
"""

import re
import os
import logging
import shutil
from urllib.parse import urljoin
import m3u8
import orjson
from configs.config import Platform
from utils.helper import get_locale, download_files
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from services.service import Service


class iTunes(Service):

    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.api = {
            'configurations': 'https://tv.apple.com/api/uts/v3/configurations?caller=web&sfh=143470&v=56&pfm=web&locale=zh-tw&ts={time}'
        }

    def get_configurations(self):
        res = self.session.get(url=self.api['configurations'])
        if res.ok:
            return res.json()['data']['applicationProps']['requiredParamsMap']
        else:
            self.logger.error(res.text)

    def parse_m3u(self, m3u_link):

        sub_url_list = []
        languages = set()
        playlists = m3u8.load(m3u_link).playlists
        for media in playlists[0].media:
            if media.type == 'SUBTITLES':
                if media.language:
                    sub_lang = media.language
                if media.forced == 'YES':
                    sub_lang += '-forced'
                if media.uri:
                    media_uri = media.uri

                sub = {}
                sub['lang'] = sub_lang

                self.logger.debug(media_uri)

                sub['urls'] = []
                if not sub_lang in languages:
                    segments = m3u8.load(media_uri)
                    for uri in segments.files:
                        sub['urls'].append(urljoin(segments.base_uri, uri))

                    languages.add(sub_lang)
                    sub_url_list.append(sub)

        return sub_url_list

    def get_subtitle(self, subtitle_list, folder_path, sub_name):

        languages = set()
        subtitles = []

        for sub in subtitle_list:
            file_name = sub_name.replace('.vtt', f".{sub['lang']}.vtt")

            lang_folder_path = os.path.join(
                folder_path, f"tmp_{file_name.replace('.vtt', '.srt')}")

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

        self.download_subtitle(subtitles=subtitles,
                               languages=languages, folder_path=folder_path)

    def download_subtitle(self, subtitles, languages, folder_path):
        if subtitles and languages:
            self.logger.debug('subtitles: %s', subtitles)
            download_files(subtitles)
            display = True
            for lang_path in sorted(languages):
                if 'tmp' in lang_path:
                    merge_subtitle_fragments(
                        folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                    display = False
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.ITUNES, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)

    def main(self):
        movie_id = os.path.basename(self.url).replace('id', '')
        headers = {
            'authority': 'itunes.apple.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-gpc': '1',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-TW,zh;q=0.9',
        }
        res = self.session.get(url=self.url, headers=headers)

        if res.ok:
            match = re.search(
                r'<script type=\"fastboot\/shoebox\" id=\"shoebox-ember-data-store\">(.+?)<\/script>', res.text)
            if match:
                movie = orjson.loads(match.group(1).strip())[movie_id]
                title = movie['data']['attributes']['name']
                release_year = movie['data']['attributes']['releaseDate'][:4]
                self.logger.info("\n%s (%s)", title, release_year)
                title = self.ripprocess.rename_file_name(
                    f'{title}.{release_year}')

                folder_path = os.path.join(self.download_path, title)

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                file_name = f'{title}.WEB-DL.{Platform.ITUNES}.vtt'

                offer_id = movie['data']['relationships']['offers']['data'][0]['id']
                m3u8_url = next(offer['attributes']['assets'][0]['hlsUrl']
                                for offer in movie['included'] if offer['type'] == 'offer' and offer['id'] == offer_id)
                self.logger.debug("m3u8_url: %s", m3u8_url)
                subtitle_list = self.parse_m3u(m3u8_url)
                self.get_subtitle(subtitle_list, folder_path, file_name)
            else:
                self.logger.error("No subtitles found!")
