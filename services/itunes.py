#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from iTunes
"""

import re
import os
import logging
import shutil
import orjson
from common.utils import Platform, get_locale, http_request, HTTPMethod, download_files, fix_filename
from common.subtitle import convert_subtitle, merge_subtitle_fragments
from services.service import Service


class iTunes(Service):

    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

    def parse_m3u(self, m3u_link):
        playlist = http_request(session=self.session,
                                url=m3u_link, method=HTTPMethod.GET, raw=True)
        sub_url_list = []
        languages = set()
        for subtitle in re.findall(r'.+TYPE=SUBTITLES.+', playlist):
            subtitle_tag = re.search(
                r'LANGUAGE=\"([^\"]+)\",.+,FORCED=(NO|YES).*,URI=\"(.+)\"', subtitle)

            forced = subtitle_tag.group(2)
            if forced == 'YES':
                sub_lang = subtitle_tag.group(1) + '-forced'
            else:
                sub_lang = subtitle_tag.group(1)

            media_uri = subtitle_tag.group(3)

            sub = {}
            sub['lang'] = sub_lang

            self.logger.debug(media_uri)

            m3u8_data = http_request(
                session=self.session, url=media_uri, method=HTTPMethod.GET, raw=True)

            sub['urls'] = []
            if not sub_lang in languages:
                for segement in re.findall(r'.+\.webvtt', m3u8_data):
                    sub_url = f'{os.path.dirname(media_uri)}/{segement}'
                    sub['urls'].append(sub_url)

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

        self.logger.debug("subtitles: %s", subtitles)
        download_files(subtitles)

        display = True
        for lang_path in sorted(languages):
            if 'tmp' in lang_path:
                merge_subtitle_fragments(
                    folder_path=lang_path, file_name=os.path.basename(lang_path.replace('tmp_', '')), lang=self.locale, display=display)
                display = False

    def download_subtitle(self):

        movie_id = os.path.basename(self.url).replace('id', '')
        metadata = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)

        match = re.search(
            r'<script type=\"fastboot\/shoebox\" id=\"shoebox-ember-data-store\">(.+?)<\/script>', metadata)
        if match:
            movie = orjson.loads(match.group(1).strip())[movie_id]
            title = movie['data']['attributes']['name']
            release_year = movie['data']['attributes']['releaseDate'][:4]
            self.logger.info("\n%s", title)
            title = fix_filename(title)

            folder_path = os.path.join(self.output, f'{title}.{release_year}')
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            file_name = f'{title}.{release_year}.WEB-DL.{Platform.ITUNES}.vtt'

            self.logger.info(
                self._("\nDownload: %s\n---------------------------------------------------------------"), file_name)

            offer_id = movie['data']['relationships']['offers']['data'][0]['id']
            m3u8_url = next(offer['attributes']['assets'][0]['hlsUrl']
                            for offer in movie['included'] if offer['type'] == 'offer' and offer['id'] == offer_id)
            self.logger.debug("m3u8_url: %s", m3u8_url)
            subtitle_list = self.parse_m3u(m3u8_url)
            self.get_subtitle(subtitle_list, folder_path, file_name)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.ITUNES, lang=self.locale)

    def main(self):
        self.download_subtitle()
