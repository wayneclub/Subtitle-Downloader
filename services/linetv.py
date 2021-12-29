"""
This module is to download subtitle from LineTV
"""

import logging
import os
import re
import requests
import shutil
from urllib.parse import quote
from time import strftime, localtime
import orjson
from bs4 import BeautifulSoup
from common.utils import http_request, HTTPMethod, check_url_exist, download_file, convert_subtitle
from common.dictionary import convert_chinese_number


class LineTV(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.url = args.url

        if args.output:
            self.output = args.output
        else:
            self.output = os.getcwd()

        if args.season:
            self.download_season = int(args.season)
        else:
            self.download_season = None

        self.last_episode = args.last_episode

        self.session = requests.Session()

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

        web_content = BeautifulSoup(response, 'lxml')

        data = orjson.loads(str(web_content.find('script').string).replace(
            'window.__INITIAL_STATE__ = ', ''))

        drama = data['entities']['dramaInfo']['byId'][drama_id]

        if drama:
            if 'drama_name' in drama:
                season_search = re.search(
                    r'(.+?)第(.+?)季', drama['drama_name'])
                if season_search:
                    drama_name = season_search.group(1).strip()
                    season_name = convert_chinese_number(
                        season_search.group(2))
                else:
                    drama_name = drama['drama_name'].strip()
                    season_name = '01'

                self.logger.info('\n%s 第 %s 季', drama_name, int(season_name))

            if 'current_eps' in drama:
                episode_num = drama['current_eps']
                folder_path = os.path.join(
                    self.output, drama_name)

                if self.last_episode:
                    drama['eps_info'] = [list(drama['eps_info'])[-1]]
                    self.logger.info('\n第 %s 季 共有：%s 集\t下載第 %s 季 最後一集\n---------------------------------------------------------------', int(
                        season_name), episode_num, int(season_name))
                else:
                    folder_path = f'{folder_path}.S{season_name}'
                    if drama['current_eps'] != drama['total_eps']:
                        self.logger.info('\n第 %s 季 共有：%s 集\t更新至 第 %s 集\t下載全集\n---------------------------------------------------------------', int(
                            season_name), drama['total_eps'], episode_num)
                    else:
                        self.logger.info('\n第 %s 季 共有：%s 集\t下載全集\n---------------------------------------------------------------', int(
                            season_name), episode_num)

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                if 'eps_info' in drama:
                    for episode in drama['eps_info']:
                        if 'number' in episode:
                            episode_name = str(episode['number'])
                            subtitle_link = self.api['sub_1'].format(
                                drama_id=drama_id, episode_name=episode_name)

                            file_name = f'{drama_name}.S{season_name}E{episode_name.zfill(2)}.WEB-DL.LineTV.zh-Hant.vtt'

                            if not check_url_exist(subtitle_link):
                                if check_url_exist(subtitle_link.replace('tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')):
                                    subtitle_link = subtitle_link.replace(
                                        'tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')
                                else:
                                    subtitle_link = self.api['sub_2'].format(
                                        drama_id=drama_id, drama_name=quote(drama_name.encode('utf8')), episode_name=episode_name)
                                    if not check_url_exist(subtitle_link):
                                        if episode['free_date']:
                                            free_date = strftime(
                                                '%Y-%m-%d', localtime(int(episode['free_date'])/1000))
                                            self.logger.info(
                                                '%s\t...一般用戶於%s開啟', file_name, free_date)

                            os.makedirs(folder_path, exist_ok=True)

                            download_file(subtitle_link, os.path.join(
                                folder_path, file_name))

                    convert_subtitle(folder_path, 'linetv')

    def main(self):
        self.download_subtitle()
