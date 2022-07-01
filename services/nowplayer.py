#!/usr/bin/python3
# coding: utf-8

"""
This module is to download video from NowPlayer
"""
import re
import sys
import logging
import os
import shutil
import time
from urllib.parse import parse_qs, urlparse
from services.service import Service
from configs.config import Platform
from utils.cookies import Cookies
from utils.subtitle import convert_subtitle


class NowPlayer(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)

        self.credential = self.config.credential(Platform.NOWPLAYER)
        self.cookies = Cookies(self.credential)

        self.access_token = ''
        self.api = {
            'series': 'https://nowplayer.now.com/vodplayer/getSeriesJson/?seriesId={series_id}',
            'movie': 'https://nowplayer.now.com/vodplayer/getProductJson/?productId={product_id}',
            'play': 'https://nowplayer.now.com/vodplayer/play/',
            'license': 'https://fwp.now.com/wrapperWV'
        }

    def generate_caller_reference_no(self):
        return f"NPXWC{int(time.time() * 1000)}"

    def movie_metadata(self, content_id):
        cookies = self.cookies.get_cookies()
        cookies['LANG'] = 'en'

        res = self.session.get(
            self.api["movie"].format(product_id=content_id), cookies=cookies)

        if res.ok:
            data = res.json()[0]

            title = data['episodeTitle']
            release_year = ""

            chinese_cookies = cookies
            chinese_cookies['LANG'] = 'zh'
            chinese_title = self.session.get(
                self.api["movie"].format(product_id=content_id), cookies=chinese_cookies).json()[0]['episodeTitle']

            movie_info = self.get_movie_info(
                title=chinese_title, title_aliases=[title])
            if movie_info:
                release_year = movie_info['release_date'][:4]

            self.logger.info("\n%s (%s) [%s]", title,
                             chinese_title, release_year)

            default_language = data['language']

            file_name = f'{title} {release_year}'

            folder_path = os.path.join(
                self.download_path, self.ripprocess.rename_file_name(file_name))

            self.download_subtitle(content_id=data['episodeId'],
                                   title=file_name, folder_path=folder_path, default_language=default_language)

            convert_subtitle(folder_path=folder_path,
                             platform=Platform.NOWPLAYER, lang=self.locale)

            if self.output:
                shutil.move(folder_path, self.output)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def series_metadata(self, content_id):
        cookies = self.cookies.get_cookies()
        cookies['LANG'] = 'en'
        res = self.session.get(
            self.api["series"].format(series_id=content_id), cookies=cookies)

        if res.ok:
            data = res.json()[0]
            title = data['brandName']
            season_index = int(data['episode'][0]['seasonNum'])
            if season_index == 0:
                season_index = 1

            season_name = str(season_index).zfill(2)

            self.logger.info("\n%s Season %s", title, season_index)

            folder_path = os.path.join(
                self.download_path, f'{self.ripprocess.rename_file_name(title)}.S{season_name}')

            episode_list = data['episode']

            episode_num = len(episode_list)

            if self.last_episode:
                episode_list = [episode_list[-1]]
                self.logger.info("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------",
                                 season_index,
                                 episode_num,
                                 season_index)
            else:
                self.logger.info("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------",
                                 season_index,
                                 episode_num)

            for episode in episode_list:
                episode_index = int(episode['episodeNum'])
                if not self.download_season or season_index in self.download_season:
                    if not self.download_episode or episode_index in self.download_episode:
                        content_id = episode['episodeId']
                        file_name = f'{title} S{season_name}E{str(episode_index).zfill(2)}'

                        self.logger.info("\n%s", file_name)

                        self.download_subtitle(content_id=content_id,
                                               title=file_name, folder_path=folder_path)

            convert_subtitle(folder_path=folder_path,
                             platform=Platform.NOWPLAYER, lang=self.locale)

            if self.output:
                shutil.move(folder_path, self.output)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def download_subtitle(self, content_id, title, folder_path, default_language=""):

        headers = {
            'user-agent': self.user_agent
        }

        cookies = self.cookies.get_cookies()

        data = {
            'callerReferenceNo': self.generate_caller_reference_no(),
            'productId': content_id,
            'isTrailer': 'false',
        }

        res = self.session.post(
            self.api["play"], headers=headers, data=data, cookies=cookies)
        if res.ok:
            data = res.json()
            if not data.get('asset'):
                if data.get('responseCode') == "NEED_LOGIN":
                    self.logger.error(
                        "Please renew the cookies, and make sure config.py USERR_AGENT is same as login browser!")
                    os.remove(self.credential['cookies_file'])
                    sys.exit(1)
                else:
                    self.logger.error("Error: %s", data.get('responseCode'))
                    sys.exit(1)
        else:
            self.logger.error("Failed to get tracks: %s", res.text)
            sys.exit(1)

        media_src = next(
            (url for url in data["asset"] if '.mpd' in url), data["asset"][0])

        if '.mpd' in media_src:
            mpd_url = media_src

            headers = {
                'user-agent': self.user_agent,
                'referer': 'https://nowplayer.now.com/'
            }

            timescale = self.ripprocess.get_time_scale(mpd_url, headers)

            self.ripprocess.download_subtitles_from_mpd(
                url=mpd_url, title=title, folder_path=folder_path, headers=headers, proxy=self.proxy, debug=self.debug, timescale=timescale)

        else:
            print()

    def main(self):
        self.cookies.load_cookies('NOWSESSIONID')

        params = parse_qs(urlparse(self.url).query)

        if params.get("id"):
            content_id = params.get("id")[0]
        else:
            self.logger.error("Unable to find content id!")
            sys.exit(1)

        if params.get("type") and params.get("type")[0] == "product":
            self.movie_metadata(content_id)
        else:
            self.series_metadata(content_id)
