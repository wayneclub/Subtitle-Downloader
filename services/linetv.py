#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from LineTV
"""

import os
import re
import shutil
import sys
from urllib.parse import quote
from time import strftime, localtime
import orjson
from cn2an import cn2an
from utils.io import rename_filename, download_files
from utils.helper import get_locale, check_url_exist
from utils.subtitle import convert_subtitle
from services.service import Service


class LineTV(Service):
    """
    Service code for Line TV streaming service (https://www.linetv.tw/).

    Authorization: None
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def series_metadata(self, data, drama_id):
        if 'drama_name' in data:
            season_search = re.search(
                r'(.+?)第(.+?)季', data['drama_name'])
            if season_search:
                title = season_search.group(1).strip()
                season_name = cn2an(
                    season_search.group(2))
            else:
                title = data['drama_name'].strip()
                season_name = '01'

            season_index = int(season_name)

            self.logger.info(self._("\n%s Season %s"), title, season_index)

        if 'current_eps' in data:
            episode_num = data['current_eps']

            name = rename_filename(f'{title}.S{str(season_index).zfill(2)}')
            folder_path = os.path.join(self.download_path, name)

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
                        episode_index = int(episode['number'])
                        if not self.download_season or season_index in self.download_season:
                            if not self.download_episode or episode_index in self.download_episode:
                                subtitle_link = self.config['api']['sub_1'].format(
                                    drama_id=drama_id, episode_name=episode_index)
                                self.logger.debug(subtitle_link)

                                filename = f'{name}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}.zh-Hant.vtt'

                                if not check_url_exist(subtitle_link):
                                    if check_url_exist(subtitle_link.replace('tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')):
                                        subtitle_link = subtitle_link.replace(
                                            'tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')
                                    else:
                                        subtitle_link = self.config['api']['sub_2'].format(
                                            drama_id=drama_id, drama_name=quote(title.encode('utf8')), episode_name=episode_index)
                                        if not check_url_exist(subtitle_link):
                                            if episode['free_date']:
                                                free_date = strftime(
                                                    '%Y-%m-%d', localtime(int(episode['free_date'])/1000))
                                                self.logger.info(
                                                    self._("%s\t...free user will be available on %s"), filename, free_date)

                                os.makedirs(folder_path, exist_ok=True)
                                subtitle = dict()
                                subtitle['name'] = filename
                                subtitle['path'] = folder_path
                                subtitle['url'] = subtitle_link
                                subtitles.append(subtitle)

                self.download_subtitle(
                    subtitles=subtitles, folder_path=folder_path)

    def download_subtitle(self, subtitles, folder_path):
        if subtitles:
            download_files(subtitles)
            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

    def main(self):
        """Download subtitle from LineTV"""

        drama_id_search = re.search(
            r'https:\/\/www\.linetv\.tw\/drama\/(.+?)\/eps\/1', self.url)

        if drama_id_search:
            drama_id = drama_id_search.group(1)
        else:
            self.logger.error("\nCan't detect content id: %s", self.url)
            sys.exit(1)

        res = self.session.get(url=self.url, timeout=5)

        if res.ok:
            match = re.search(
                r'window\.__INITIAL_STATE__ = (\{.*\})', res.text)

            if match:
                data = orjson.loads(match.group(1))
                data = data['entities']['dramaInfo']['byId'][drama_id]
                self.series_metadata(data, drama_id)
        else:
            self.logger.error(res.text)
