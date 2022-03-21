#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from LineTV
"""

import logging
import os
import re
import shutil
import sys
from urllib.parse import quote
from time import strftime, localtime
import orjson
from configs.config import Platform
from utils.helper import get_locale, check_url_exist, download_files
from utils.dictionary import convert_chinese_number
from utils.subtitle import convert_subtitle
from services.service import Service


class LineTV(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)
        self._ = get_locale(__name__, self.locale)

        self.api = {
            'sub_1': 'https://s3-ap-northeast-1.amazonaws.com/tv-aws-media-convert-input-tokyo/subtitles/{drama_id}/{drama_id}-eps-{episode_name}.vtt',
            'sub_2': 'https://choco-tv.s3.amazonaws.com/subtitle/{drama_id}-{drama_name}/{drama_id}-eps-{episode_name}.vtt'
        }

    def series_metadata(self, data, drama_id):
        if 'drama_name' in data:
            season_search = re.search(
                r'(.+?)第(.+?)季', data['drama_name'])
            if season_search:
                title = season_search.group(1).strip()
                season_name = convert_chinese_number(
                    season_search.group(2))
            else:
                title = data['drama_name'].strip()
                season_name = '01'

            season_index = int(season_name)

            self.logger.info(self._("\n%s Season %s"), title, season_index)

        if 'current_eps' in data:
            episode_num = data['current_eps']

            folder_path = os.path.join(
                self.download_path, f'{self.ripprocess.rename_file_name(title)}.S{season_name}')

            if self.last_episode:
                data['eps_info'] = [list(data['eps_info'])[-1]]
                self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                 season_index,
                                 episode_num,
                                 season_index)
            else:
                if data['current_eps'] != data['total_eps']:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                     season_index,
                                     data['total_eps'],
                                     episode_num)
                else:
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                     season_index,
                                     episode_num)

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            if 'eps_info' in data:
                subtitles = []
                for episode in data['eps_info']:
                    if 'number' in episode:
                        episode_index = episode['number']
                        if not self.download_season or season_index in self.download_season:
                            if not self.download_episode or episode['episode_index'] in self.download_episode:
                                subtitle_link = self.api['sub_1'].format(
                                    drama_id=drama_id, episode_name=episode_index)
                                self.logger.debug(subtitle_link)

                                file_name = f'{title}.S{season_name}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.LINETV}.zh-Hant.vtt'

                                if not check_url_exist(subtitle_link):
                                    if check_url_exist(subtitle_link.replace('tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')):
                                        subtitle_link = subtitle_link.replace(
                                            'tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')
                                    else:
                                        subtitle_link = self.api['sub_2'].format(
                                            drama_id=drama_id, drama_name=quote(title.encode('utf8')), episode_name=episode_index)
                                        if not check_url_exist(subtitle_link):
                                            if episode['free_date']:
                                                free_date = strftime(
                                                    '%Y-%m-%d', localtime(int(episode['free_date'])/1000))
                                                self.logger.info(
                                                    self._("%s\t...free user will be available on %s"), file_name, free_date)

                                os.makedirs(folder_path, exist_ok=True)
                                subtitle = dict()
                                subtitle['name'] = file_name
                                subtitle['path'] = folder_path
                                subtitle['url'] = subtitle_link
                                subtitles.append(subtitle)

                self.download_subtitle(
                    subtitles=subtitles, folder_path=folder_path)

    def download_subtitle(self, subtitles, folder_path):
        if subtitles:
            download_files(subtitles)
            convert_subtitle(folder_path=folder_path,
                             platform=Platform.LINETV, lang=self.locale)
            if self.output:
                shutil.move(folder_path, self.output)

    def main(self):
        """Download subtitle from LineTV"""

        drama_id_search = re.search(
            r'https:\/\/www\.linetv\.tw\/drama\/(.+?)\/eps\/1', self.url)

        if drama_id_search:
            drama_id = drama_id_search.group(1)
        else:
            self.logger.error("\nCan't detect content id: %s", self.url)
            sys.exit(-1)

        res = self.session.get(url=self.url)

        if res.ok:
            match = re.search(
                r'window\.__INITIAL_STATE__ = (\{.*\})', res.text)

            if match:
                data = orjson.loads(match.group(1))
                data = data['entities']['dramaInfo']['byId'][drama_id]
                self.series_metadata(data, drama_id)
        else:
            self.logger.error(res.text)
