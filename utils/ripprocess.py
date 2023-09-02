#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from rip media streams
"""
import logging
import os
import shutil
import re
import glob
from pathlib import Path
from urllib.parse import urlparse
import requests
import orjson
from configs.config import user_agent
from constants import LANGUAGE_LIST
from utils.subtitle import merge_subtitle_fragments
from utils.helper import get_language_code
from tools.XstreamDL_CLI.extractor import Extractor
from tools.XstreamDL_CLI.downloader import Downloader
from tools.pyshaka.main import parse


class XstreamArgs(object):
    """
    XstreamDL_CLI args
    """

    def __init__(self, save_dir, url_patch, headers, proxy, log_level):
        self.speed_up = False
        self.speed_up_left = 10
        self.live = False
        self.compare_with_url = False
        self.dont_split_discontinuity = False
        self.name_from_url = False
        self.live_duration = 0.0
        self.live_utc_offset = 0
        self.live_refresh_interval = 3
        self.name = 'dash'
        self.base_url = ''
        self.ad_keyword = ''
        self.resolution = ''
        self.best_quality = False
        self.video_only = False
        self.audio_only = False
        self.all_videos = False
        self.all_audios = False
        self.service = ''
        self.save_dir = Path(save_dir)
        self.select = False
        self.multi_s = False
        self.disable_force_close = True
        self.limit_per_host = 10
        self.headers = headers
        self.url_patch = url_patch
        self.overwrite = False
        self.raw_concat = False
        self.disable_auto_concat = False
        self.enable_auto_delete = True
        self.disable_auto_decrypt = False
        self.key = None
        self.b64key = None
        self.hexiv = None
        self.proxy = proxy
        self.disable_auto_exit = False
        self.parse_only = False
        self.show_init = False
        self.index_to_name = False
        self.log_level = 'INFO'
        self.redl_code = []  # type: list
        self.hide_load_metadata = True  # type: bool
        self.no_metadata_file = None  # type: bool
        self.gen_init_only = False  # type: bool
        self.skip_gen_init = None  # type: bool
        self.URI = None  # type: list


class PyshakaArgs(object):
    """
    Pyshaka args
    """

    def __init__(self, segments_path, log_level):
        self.type = 'wvtt'
        self.init_path = os.path.join(segments_path, 'init.mp4')
        self.segments_path = segments_path
        self.debug = True if log_level == logging.DEBUG else False
        self.segment_time = 0


class RipProcess(object):
    """
    Rip process
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def download_subtitles_from_mpd(self, url, title, folder_path, url_patch=False, headers="", proxy="", log_level=logging.INFO, timescale=""):
        """Download  subtitles from mpd url"""
        os.makedirs(folder_path, exist_ok=True)

        if not headers:
            headers = {
                'user-agent': user_agent
            }

        if url_patch:
            url_patch = f"?{urlparse(url).query}"
        else:
            url_patch = ""

        args = XstreamArgs(save_dir=folder_path, url_patch=url_patch,
                           headers=headers, proxy=proxy, log_level=log_level)

        args.disable_auto_concat = True
        args.enable_auto_delete = False

        extractor = Extractor(args)
        streams = extractor.fetch_metadata(url)

        sub_tracks = set()
        for index, stream in enumerate(streams):
            self.logger.debug(
                '%s %s', index, f"{stream.get_name()}{stream.get_init_msg(False)}")
            if 'subtitle' in f"{stream.get_name()}{stream.get_init_msg(False)}":
                sub_tracks.add(index)

        if not sub_tracks:
            self.logger.error(
                "\nSorry, there's no embedded subtitles in this video!")
            return

        Downloader(args).download_streams(streams, sub_tracks)

        for segments_path in glob.glob(os.path.join(folder_path, "*subtitle*")):
            subtitle_language = re.findall(
                r'_subtitle_.+?_([^_\.]+)', segments_path)[0]
            subtitle_language = get_language_code(
                subtitle_language)

            subtitle_language = next((
                language[1] for language in LANGUAGE_LIST if subtitle_language in language), subtitle_language)
            file_name = f"{title}.{subtitle_language}.vtt"
            if os.path.exists(os.path.join(segments_path, 'init.mp4')):
                if os.path.isdir(segments_path):
                    self.extract_sub(segments_path, self.logger.level)

                    os.rename(f"{segments_path}.vtt",
                              os.path.join(folder_path, file_name))
            else:
                with open(os.path.join(segments_path, 'raw.json'), 'rb') as file:
                    content = file.read().decode('utf-8')

                shift_time = []
                if timescale:
                    for sub in orjson.loads(content)['segments']:
                        seg_num = os.path.basename(sub['url']).replace(
                            Path(sub['url']).suffix, '').split('-')[1]
                        offset = int(seg_num) / timescale
                        shift_time.append({
                            'name': sub['name'],
                            'offset': offset
                        })
                merge_subtitle_fragments(
                    folder_path=segments_path, file_name=file_name, shift_time=shift_time)

        for path in glob.glob(os.path.join(folder_path, "dash*")):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def extract_sub(self, segments_path, log_level):
        """Call pyshaka"""

        args = PyshakaArgs(segments_path, log_level)
        parse(args)

    def get_time_scale(self, mpd_url, headers):
        """Get time scale"""

        res = requests.get(url=mpd_url, headers=headers, timeout=5)
        if res.ok:
            timescale = re.search(r'(?<=timescale=\")\d*(?=\")', res.text)
            return float(timescale.group())
        else:
            self.logger.error(res.text)
