#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from LineTV
"""

import logging
import os
import re
import shutil
from urllib.parse import quote
from time import strftime, localtime
import orjson
from common.utils import get_locale, Platform, http_request, HTTPMethod, check_url_exist, download_files
from common.dictionary import convert_chinese_number
from common.subtitle import convert_subtitle
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

    def download_subtitle(self):
        """Download subtitle from LineTV"""

        drama_id_search = re.search(
            r'https:\/\/www\.linetv\.tw\/drama\/(.+?)\/eps\/1', self.url)
        drama_id = drama_id_search.group(1)

        response = http_request(session=self.session,
                                url=self.url, method=HTTPMethod.GET, raw=True)

        match = re.search(r'window\.__INITIAL_STATE__ = (\{.*\})', response)

        data = orjson.loads(match.group(1))

        drama = data['entities']['dramaInfo']['byId'][drama_id]

        if drama:
            if 'drama_name' in drama:
                season_search = re.search(
                    r'(.+?)第(.+?)季', drama['drama_name'])
                if season_search:
                    title = season_search.group(1).strip()
                    season_name = convert_chinese_number(
                        season_search.group(2))
                else:
                    title = drama['drama_name'].strip()
                    season_name = '01'

                self.logger.info(self._("\n%s Season %s"),
                                 title, int(season_name))

            if 'current_eps' in drama:
                episode_num = drama['current_eps']
                folder_path = os.path.join(
                    self.output, f'{title}.S{season_name}')

                if self.last_episode:
                    drama['eps_info'] = [list(drama['eps_info'])[-1]]
                    self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                                     int(season_name),
                                     episode_num,
                                     int(season_name))
                else:
                    if drama['current_eps'] != drama['total_eps']:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tupdate to episode %s\tdownload all episodes\n---------------------------------------------------------------"),
                                         int(season_name),
                                         drama['total_eps'],
                                         episode_num)
                    else:
                        self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                                         int(season_name),
                                         episode_num)

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                if 'eps_info' in drama:
                    subtitles = []
                    for episode in drama['eps_info']:
                        if 'number' in episode:
                            episode_name = str(episode['number'])
                            subtitle_link = self.api['sub_1'].format(
                                drama_id=drama_id, episode_name=episode_name)
                            self.logger.debug(subtitle_link)

                            file_name = f'{title}.S{season_name}E{episode_name.zfill(2)}.WEB-DL.{Platform.LINETV}.zh-Hant.vtt'

                            if not check_url_exist(subtitle_link):
                                if check_url_exist(subtitle_link.replace('tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')):
                                    subtitle_link = subtitle_link.replace(
                                        'tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')
                                else:
                                    subtitle_link = self.api['sub_2'].format(
                                        drama_id=drama_id, drama_name=quote(title.encode('utf8')), episode_name=episode_name)
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

                    download_files(subtitles)
                    convert_subtitle(folder_path=folder_path,
                                     ott=Platform.LINETV, lang=self.locale)

    def main(self):
        self.download_subtitle()
