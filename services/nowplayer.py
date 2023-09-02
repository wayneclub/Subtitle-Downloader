#!/usr/bin/python3
# coding: utf-8

"""
This module is to download video from NowPlayer
"""
from pathlib import Path
import shutil
import sys
import os
import time
from urllib.parse import parse_qs, urlparse
from requests.utils import cookiejar_from_dict
from configs.config import config, credentials, user_agent
from utils.helper import get_locale
from utils.io import rename_filename
from utils.subtitle import convert_subtitle
from services.service import Service


class NowPlayer(Service):
    """
    Service code for Now Player streaming service (https://www.nowtv.now.com/).

    Authorization: Cookies
    """

    def __init__(self, args):
        super().__init__(args)
        self._ = get_locale(__name__, self.locale)

    def generate_caller_reference_no(self):
        return f"NPXWC{int(time.time() * 1000)}"

    def movie_metadata(self, content_id):
        self.cookies['LANG'] = 'en'
        self.session.cookies.update(cookiejar_from_dict(
            self.cookies, cookiejar=None, overwrite=True))

        res = self.session.get(
            self.config['api']['movie'].format(product_id=content_id), timeout=5)

        if res.ok:
            data = res.json()[0]

            title = data['episodeTitle']
            release_year = ""

            chinese_cookies = self.cookies
            chinese_cookies['LANG'] = 'zh'
            self.session.cookies.update(cookiejar_from_dict(
                chinese_cookies, cookiejar=None, overwrite=True))
            chinese_title = self.session.get(
                self.config['api']['movie'].format(product_id=content_id), timeout=5).json()[0]['episodeTitle']

            release_year = ''
            movie_info = self.get_title_info(
                title=chinese_title, title_aliases=[title])
            if movie_info:
                release_year = movie_info['release_date'][:4]

            if release_year:
                self.logger.info("\n%s (%s)", title, release_year)
            else:
                self.logger.info("\n%s", title)

            # default_language = data['language']

            title = rename_filename(f'{title}.{release_year}')
            folder_path = os.path.join(self.download_path, title)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            filename = f'{title}.WEB-DL.{self.platform}'

            self.download_subtitle(
                content_id=data['episodeId'], title=filename, folder_path=folder_path)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def series_metadata(self, content_id):
        self.cookies['LANG'] = 'en'
        self.session.cookies.update(cookiejar_from_dict(
            self.cookies, cookiejar=None, overwrite=True))

        res = self.session.get(
            self.config['api']["series"].format(series_id=content_id), timeout=5)

        if res.ok:
            data = res.json()[0]
            title = data['brandName']
            season_index = int(data['episode'][0]['seasonNum'])
            if season_index == 0:
                season_index = 1

            self.logger.info("\n%s Season %s", title, season_index)

            name = rename_filename(f'{title}.S{str(season_index).zfill(2)}')
            folder_path = os.path.join(self.download_path, name)

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
                        filename = f'{name}E{str(episode_index).zfill(2)}'

                        self.logger.info("\n%s", filename)

                        self.download_subtitle(content_id=content_id,
                                               title=filename, folder_path=folder_path)

            convert_subtitle(folder_path=folder_path,
                             platform=self.platform, subtitle_format=self.subtitle_format, locale=self.locale)

        else:
            self.logger.error(res.text)
            sys.exit(1)

    def download_subtitle(self, content_id, title, folder_path):
        data = {
            'callerReferenceNo': self.generate_caller_reference_no(),
            'productId': content_id,
            'isTrailer': 'false',
        }

        res = self.session.post(
            self.config['api']["play"], data=data)
        if res.ok:
            data = res.json()
            if not data.get('asset'):
                if data.get('responseCode') == "NEED_LOGIN":
                    self.logger.error(
                        self._("\nPlease renew the cookies, and make sure user_config.toml's User-Agent is same as %s in the browser!"), self.platform)
                    os.remove(
                        Path(config.directories['cookies']) / credentials[self.platform]['cookies'])
                    sys.exit(1)
                else:
                    self.logger.error("Error: %s", data.get('responseCode'))
                    sys.exit(1)
        else:
            self.logger.error(self._("Failed to get tracks: %s"), res.text)
            sys.exit(1)

        media_src = next(
            (url for url in data["asset"] if '.mpd' in url), data["asset"][0])

        if '.mpd' in media_src:
            mpd_url = media_src

            headers = {
                'user-agent': user_agent,
                'referer': 'https://nowplayer.now.com/'
            }

            timescale = self.ripprocess.get_time_scale(mpd_url, headers)

            self.ripprocess.download_subtitles_from_mpd(
                url=mpd_url, title=title, folder_path=folder_path, headers=headers, proxy=self.proxy, log_level=self.logger.level, timescale=timescale)

        else:
            sys.exit()

    def main(self):
        params = parse_qs(urlparse(self.url).query)

        if params.get('id'):
            content_id = params.get('id')[0]
        else:
            self.logger.error(
                "\nUnable to find content id, Please check the url is valid.")
            sys.exit(1)

        if params.get('type') and params.get('type')[0] == 'product':
            self.movie_metadata(content_id)
        else:
            self.series_metadata(content_id)
