"""
This module is to download subtitle from KKTV
"""
import logging
import os
import re
import requests
import shutil
import orjson
from bs4 import BeautifulSoup
from common.utils import http_request, HTTPMethod, check_url_exist, download_file, convert_subtitle, save_html


class KKTV(object):
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
            'play': 'https://www.kktv.me/play/{drama_id}010001'
        }

    def download_subtitle(self):

        drama_id = os.path.basename(self.url)

        play_url = self.api['play'].format(drama_id=drama_id)

        response = http_request(session=self.session,
                                url=play_url, method=HTTPMethod.GET, raw=True)

        web_content = BeautifulSoup(response, 'lxml')

        data = orjson.loads(str(web_content.find(
            'script', id='__NEXT_DATA__').string))

        drama = data['props']['initialState']['titles']['byId'][drama_id]

        if drama:
            if 'title' in drama:
                drama_name = drama['title']

            if 'titleType' in drama and drama['titleType'] == 'film':
                film = True
            else:
                film = False

            anime = False
            if 'genres' in drama:
                for genre in drama['genres']:
                    if 'title' in genre and genre['title'] == '動漫':
                        anime = True

            if 'totalSeriesCount' in drama:
                season_num = drama['totalSeriesCount']

            if film or anime:
                self.logger.info('\n%s', drama_name)
            else:
                if 'dual_subtitle' in drama['contentLabels']:
                    self.logger.info('\n%s 共有： %s 季（有提供雙語字幕）',
                                     drama_name, season_num)
                else:
                    self.logger.info('\n%s 共有： %s 季', drama_name, season_num)

            if 'series' in drama:
                for season in drama['series']:
                    season_index = int(season['title'][1])
                    if not self.download_season or season_index == self.download_season:
                        season_name = str(season_index).zfill(2)
                        episode_num = len(season['episodes'])

                        folder_path = os.path.join(self.output, drama_name)

                        if film:
                            self.logger.info(
                                '\n下載電影\n---------------------------------------------------------------')
                        elif self.last_episode:
                            self.logger.info(
                                '\n第 %s 季 共有：%s 集\t下載第 %s 季 最後一集\n---------------------------------------------------------------', season_index, episode_num, season_index)

                            season['episodes'] = [list(season['episodes'])[-1]]
                        elif anime:
                            self.logger.info(
                                '\n共有：%s 集\t下載全集\n---------------------------------------------------------------', episode_num)
                        else:
                            self.logger.info(
                                '\n第 %s 季 共有：%s 集\t下載全集\n---------------------------------------------------------------', season_index, episode_num)
                            folder_path = f'{folder_path}.S{season_name}'

                        if os.path.exists(folder_path):
                            shutil.rmtree(folder_path)

                        jp_lang = False
                        ko_lang = False
                        for episode in season['episodes']:
                            episode_index = int(
                                episode['id'].replace(episode['seriesId'], ''))
                            if len(season['episodes']) < 100:
                                episode_name = str(episode_index).zfill(2)
                            else:
                                episode_name = str(episode_index).zfill(3)

                            if not episode['subtitles']:
                                self.logger.info('\n無提供可下載的字幕\n')
                                exit()
                            if 'ja' in episode['subtitles']:
                                jp_lang = True
                            if 'ko' in episode['subtitles']:
                                ko_lang = True

                            episode_uri = episode['mezzanines']['dash']['uri']
                            if episode_uri:
                                episode_link_search = re.search(
                                    r'https:\/\/theater\.kktv\.com\.tw([^"]+)_dash\.mpd', episode_uri)
                                if episode_link_search:
                                    episode_link = episode_link_search.group(
                                        1)
                                    epsiode_search = re.search(
                                        drama_id + '[0-9]{2}([0-9]{4})_', episode_uri)
                                    if epsiode_search:
                                        subtitle_link = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/zh-Hant.vtt'

                                        ja_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ja.vtt')

                                        ko_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ko.vtt')

                                        if film:
                                            file_name = f'{drama_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                        elif anime:
                                            file_name = f'{drama_name}E{episode_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                        else:
                                            file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                            ja_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ja.vtt')
                                            ko_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ko.vtt')

                                            ja_folder_path = os.path.join(
                                                folder_path, '日語')
                                            ko_folder_path = os.path.join(
                                                folder_path, '韓語')

                                        os.makedirs(
                                            folder_path, exist_ok=True)

                                        if jp_lang:
                                            os.makedirs(
                                                ja_folder_path, exist_ok=True)

                                        if ko_lang:
                                            os.makedirs(
                                                ko_folder_path, exist_ok=True)

                                        download_file(subtitle_link, os.path.join(
                                            folder_path, os.path.basename(file_name)))

                                        if jp_lang and check_url_exist(ja_subtitle_link):
                                            download_file(ja_subtitle_link, os.path.join(
                                                ja_folder_path, os.path.basename(ja_file_name)))

                                        if ko_lang and check_url_exist(ko_subtitle_link):
                                            download_file(ko_subtitle_link, os.path.join(
                                                ko_folder_path, os.path.basename(ko_file_name)))

                        if jp_lang:
                            convert_subtitle(ja_folder_path)
                        if ko_lang:
                            convert_subtitle(ko_folder_path)

                        convert_subtitle(folder_path, 'kktv')

    def main(self):
        self.download_subtitle()
