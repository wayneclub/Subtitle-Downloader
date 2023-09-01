#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitles from NowE
"""
import math
from pathlib import Path
import random
import sys
import os
import re
import shutil
import time
from cn2an import cn2an
from configs.config import config, credentials, user_agent
from utils.helper import get_locale
from utils.io import rename_filename
from utils.subtitle import convert_subtitle
from services.service import Service


class NowE(Service):
    """
    Service code for Now E streaming service (https://www.nowe.com/).

    Authorization: Cookies
    """

    GEOFENCE = ['hk']

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def generate_caller_reference_no(self):
        return f"W{int(time.time() * 1000)}{math.floor((1 + random.random()) * 900) + 100}"

    def update_session(self):

        session_id = self.cookies.get('OTTSESSIONID')
        device_id = self.cookies.get('NMAF_uuid')

        payload = {
            'deviceId': device_id,
            'deviceType': 'WEB',
            'secureCookie': session_id,
            'profileId': session_id,
            'callerReferenceNo': self.generate_caller_reference_no()
        }

        update_session_url = self.config['api']['update_session']

        res = self.session.post(
            url=update_session_url, json=payload)

        if res.ok:
            data = res.json()
            if 'OTTSESSIONID' in data:
                return data['OTTSESSIONID']
            else:
                self.logger.error(
                    self._("\nPlease renew the cookies, and make sure user_config.toml's User-Agent is same as %s in the browser!"), self.platform)
                os.remove(
                    Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
                sys.exit(1)
        else:
            self.logger.error(res.text)

    def get_metadata(self, content_id):
        payload = {
            'lang': 'zh',
            'productIdList': [content_id],
            'callerReferenceNo': self.generate_caller_reference_no()
        }

        product_detail_url = self.config['api']['product_detail']

        res = self.session.post(
            url=product_detail_url, json=payload)

        if res.ok:
            return res.json()['productDetailList'][0]
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def movie_metadata(self, data):
        title = data['brandName'].replace('Now 爆谷台呈獻: ', '')
        content_id = data['episodeId']

        release_year = ''
        movie_info = self.get_title_info(
            title=title, title_aliases=[title])
        if movie_info:
            release_year = movie_info['release_date'][:4]

        if release_year:
            self.logger.info("\n%s (%s)", title, release_year)
        else:
            self.logger.info("\n%s", title)

        title = rename_filename(f'{title}.{release_year}')
        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{self.platform}'

        self.download_subtitle(content_id=content_id,
                               title=file_name, folder_path=folder_path)

        convert_subtitle(folder_path=folder_path,
                         platform=self.platform, lang=self.locale)

    def series_metadata(self, data):
        title = data['brandName']
        season_index = int(data['seasonNum'])
        if season_index == 0:
            season_search = re.search(
                r'(.+?)第(.+?)季', data['brandName'])
            if season_search:
                title = season_search.group(1).strip()
                season_index = int(cn2an(season_search.group(2)))
            else:
                title = data['brandName'].strip()
                season_index = 1

        self.logger.info(self._("\n%s Season %s"), title, season_index)
        title = rename_filename(
            f'{title}.S{str(season_index).zfill(2)}')
        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        episode_list = data['episode']

        episode_num = len(episode_list)

        if self.last_episode:
            episode_list = [episode_list[-1]]
            self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------"),
                             season_index,
                             episode_num,
                             season_index)
        elif self.download_episode:
            self.logger.info(
                self._("\nSeason %s total: %s episode(s)\tdownload episode: %s\n---------------------------------------------------------------"), season_index, episode_num, self.download_episode)
        else:
            self.logger.info(self._("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------"),
                             season_index,
                             episode_num)

        for episode in episode_list:
            episode_index = int(episode['episodeNum'])
            if not self.download_season or season_index in self.download_season:
                if not self.download_episode or episode_index in self.download_episode:
                    content_id = episode['episodeId']
                    file_name = f'{title}E{str(episode_index).zfill(2)}.WEB-DL.{self.platform}'

                    self.logger.info("\n%s", file_name)

                    self.download_subtitle(content_id=content_id,
                                           title=file_name, folder_path=folder_path)

        convert_subtitle(folder_path=folder_path,
                         platform=self.platform, lang=self.locale)

    def download_subtitle(self, content_id, title, folder_path):

        device_id = self.cookies.get('NMAF_uuid')

        session_id = self.update_session()

        payload = {
            'callerReferenceNo': self.generate_caller_reference_no(),
            'contentId': content_id,
            'contentType': 'Vod',
            'deviceName': 'Browser',
            'deviceId': device_id,
            'deviceType': 'WEB',
            'pin': '',
            'secureCookie': session_id,
            'profileId': session_id
        }

        media_info_url = self.config['api']['get_vod']
        res = self.session.post(
            url=media_info_url, json=payload)

        if res.ok:
            data = res.json()
            if data['responseCode'] != 'SUCCESS':
                if data['responseCode'] == 'NEED_SUB':
                    self.logger.error(
                        self._("\nPlease check your subscription plan, and make sure you are able to watch it online!"))
                else:
                    self.logger.error("Error: %s", data['responseCode'])
                sys.exit(1)

            self.logger.debug("media_info: %s", data)

            mpd_url = data['asset']

            timescale = self.ripprocess.get_time_scale(mpd_url=mpd_url, headers={
                'user-agent': user_agent
            })

            self.ripprocess.download_subtitles_from_mpd(
                url=mpd_url, title=title, folder_path=folder_path, timescale=timescale)

        else:
            self.logger.error(res.text)

    def main(self):

        content_id = re.search(r'(season|movie)\/([^\/]+)', self.url)
        if not content_id:
            self.logger.error(self._("Unable to find content id!"))
            sys.exit(1)

        content_id = content_id.group(2).strip()

        data = self.get_metadata(content_id)
        if 'movie' in self.url:
            self.movie_metadata(data)
        else:
            self.series_metadata(data)
