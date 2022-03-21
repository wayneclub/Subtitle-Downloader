#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitles from NowE
"""
import math
import random
import sys
import logging
import os
import re
import shutil
import time
from services.service import Service
from configs.config import Platform
from utils.cookies import Cookies
from utils.subtitle import convert_subtitle


class NowE(Service):
    def __init__(self, args):
        super().__init__(args)
        self.logger = logging.getLogger(__name__)

        self.credential = self.config.credential(Platform.NOWE)
        self.cookies = Cookies(self.credential)

        self.access_token = ''
        self.api = {
            'product_detail': 'https://bridge.nowe.com/BridgeEngine/getProductDetail',
            'update_session': 'https://webtvapi.nowe.com/16/1/updateSession',
            'get_vod': 'https://webtvapi.nowe.com/16/1/getVodURL'
        }

    def generate_caller_reference_no(self):
        return f"W{int(time.time() * 1000)}{math.floor((1 + random.random()) * 900) + 100}"

    def update_session(self):

        headers = {
            'user-agent': self.credential['user_agent']
        }

        cookies = self.cookies.get_cookies()

        session_id = cookies.get('OTTSESSIONID')
        device_id = cookies.get('NMAF_uuid')

        payload = {
            'deviceId': device_id,
            'deviceType': 'WEB',
            'secureCookie': session_id,
            'profileId': session_id,
            'callerReferenceNo': self.generate_caller_reference_no()
        }

        update_session_url = self.api['update_session']

        res = self.session.post(
            url=update_session_url, headers=headers, json=payload)

        if res.ok:
            data = res.json()
            if 'OTTSESSIONID' in data:
                return data['OTTSESSIONID']
            else:
                self.logger.error(
                    "Please renew the cookies, and make sure config.py NowE's user_agent is same as login browser!")
                os.remove(self.credential['cookies_file'])
                sys.exit(1)
        else:
            self.logger.error(res.text)

    def get_metadata(self, content_id):
        headers = {
            'user-agent': self.credential['user_agent']
        }

        payload = {
            'lang': 'zh',
            'productIdList': [content_id],
            'callerReferenceNo': self.generate_caller_reference_no()
        }

        product_detail_url = self.api['product_detail']

        res = self.session.post(
            url=product_detail_url, headers=headers, json=payload)

        if res.ok:
            return res.json()['productDetailList'][0]
        else:
            self.logger.error(res.text)
            sys.exit(1)

    def movie_metadata(self, data):
        title = data['brandName'].replace('Now 爆谷台呈獻: ', '')
        content_id = data['episodeId']
        self.logger.info("\n%s", title)

        title = self.ripprocess.rename_file_name(title)
        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        file_name = f'{title}.WEB-DL.{Platform.NOWE}'

        self.download_subtitle(content_id=content_id,
                               title=file_name, folder_path=folder_path)

    def series_metadata(self, data):
        title = data['episode'][0]['brandName']
        season_index = data['episode'][0]['seasonNum']

        self.logger.info("\n%s Season %s", title, season_index)
        title = self.ripprocess.rename_file_name(
            f'{title}.S{str(season_index).zfill(2)}')
        folder_path = os.path.join(self.download_path, title)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        episode_list = data['episode']

        episode_num = len(episode_list)

        if self.last_episode:
            episode_list = [episode_list[-1]]
            self.logger.info("\nSeason %s total: %s episode(s)\tdownload season %s last episode\n---------------------------------------------------------------",
                             season_index,
                             episode_num,
                             season_index)
        elif self.download_episode:
            self.logger.info(
                "\nSeason %s total: %s episode(s)\tdownload episode: %s\n---------------------------------------------------------------", season_index, episode_num, self.download_episode)
        else:
            self.logger.info("\nSeason %s total: %s episode(s)\tdownload all episodes\n---------------------------------------------------------------",
                             season_index,
                             episode_num)

        for episode in episode_list:
            episode_index = episode['episodeNum']
            if not self.download_season or season_index in self.download_season:
                if not self.download_episode or episode_index in self.download_episode:
                    content_id = episode['episodeId']
                    file_name = f'{title}E{str(episode_index).zfill(2)}.WEB-DL.{Platform.NOWE}'

                    self.logger.info("\n%s", file_name)

                    self.download_subtitle(content_id=content_id,
                                           title=file_name, folder_path=folder_path)

    def download_subtitle(self, content_id, title, folder_path):

        headers = {
            'user-agent': self.credential['user_agent']
        }

        cookies = self.cookies.get_cookies()
        device_id = cookies.get('NMAF_uuid')

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

        media_info_url = self.api['get_vod']
        res = self.session.post(
            url=media_info_url, headers=headers, json=payload)

        if res.ok:
            data = res.json()
            if data['responseCode'] != 'SUCCESS':
                if data['responseCode'] == 'NEED_SUB':
                    self.logger.error(
                        "Please check your subscription plan, and make sure you are able to watch it online!")
                else:
                    self.logger.error("Error: %s", data['responseCode'])
                sys.exit(1)

            self.logger.debug("media_info: %s", data)

            mpd_url = data['asset']

            timescale = self.ripprocess.get_time_scale(mpd_url, headers)

            self.ripprocess.download_subtitles_from_mpd(
                url=mpd_url, title=title, folder_path=folder_path, proxy=self.proxy, timescale=timescale)

            convert_subtitle(folder_path=folder_path,
                             platform=Platform.NOWE, lang=self.locale)

            if self.output:
                shutil.move(folder_path, self.output)

        else:
            self.logger.error(res.text)

    def main(self):
        self.cookies.load_cookies('OTTSESSIONID')

        content_id = re.search(r'(season|movie)\/([^\/]+)', self.url)
        if not content_id:
            self.logger.error("Unable to find content id!")
            sys.exit(1)

        content_id = content_id.group(2).strip()

        data = self.get_metadata(content_id)
        if 'movie' in self.url:
            self.movie_metadata(data)
        else:
            self.series_metadata(data)
