#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from rip media streams
"""
from email import header
import logging
import os
import shutil
import sys
import re
import glob
from subprocess import check_output
from pathlib import Path
from urllib.parse import urlparse, urljoin
import time
import requests
import orjson
from configs.config import Config
from utils.subtitle import convert_subtitle, merge_subtitle_fragments
from tools.XstreamDL_CLI.extractor import Extractor
from tools.XstreamDL_CLI.downloader import Downloader
from tools.pyshaka.main import parse


class ripprocess(object):
    def __init__(self):
        self.config = Config()
        self.user_agent = self.config.get_user_agent()
        self.logger = logging.getLogger(__name__)
        self.language_list = self.config.language_list()

    def download_subtitles_from_mpd(self, url, title, folder_path, url_patch=False, headers="", proxy="", debug=False, timescale=""):
        self.logger.info("\nDownloading subtitles...")

        os.makedirs(folder_path, exist_ok=True)

        if not header:
            headers = {
                'user-agent': self.user_agent
            }

        if url_patch:
            url_patch = f"?{urlparse(url).query}"
        else:
            url_patch = ""

        class Args(object):
            def __init__(self, url_patch, headers, proxy, debug):
                self.proxy = proxy
                self.headers = headers
                self.base_url = ''
                self.name = 'dash'
                self.name_from_url = ''
                self.url_patch = url_patch
                self.live = False
                self.parse_only = False
                self.multi_s = False
                self.select = False
                self.save_dir = Path(folder_path)
                self.limit_per_host = 10
                self.disable_force_close = True
                self.disable_auto_concat = True
                self.disable_auto_decrypt = False
                self.speed_up = True
                self.speed_up_left = 10
                self.best_quality = False
                self.show_init = False
                self.index_to_name = False
                self.redl_code = []
                self.resolution = ''
                self.audio_only = False
                self.video_only = False
                self.overwrite = False
                self.enable_auto_delete = False
                self.hide_load_metadata = True
                self.all_videos = False
                self.all_audios = False
                self.ad_keyword = ''
                self.key = None
                self.b64key = None
                self.hexiv = None
                self.raw_concat = None
                self.log_level = 'DEBUG' if debug else 'INFO'

        args = Args(url_patch=url_patch, headers=headers,
                    proxy=proxy, debug=debug)

        extractor = Extractor(args)
        streams = extractor.fetch_metadata(url)

        sub_tracks = set()
        for index, stream in enumerate(streams):
            self.logger.debug(
                index, f"{stream.get_name()}{stream.get_init_msg(False)}")
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
            subtitle_language = self.config.get_language_code(
                subtitle_language)

            subtitle_language = next((
                language[1] for language in self.language_list if subtitle_language in language), subtitle_language)
            file_name = f"{title}.{subtitle_language}.vtt"
            if os.path.exists(os.path.join(segments_path, 'init.mp4')):
                if os.path.isdir(segments_path):
                    self.extract_sub(segments_path, debug)

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

        return convert_subtitle(folder_path=folder_path)

    def extract_sub(self, segments_path, debug):
        class Attr(object):
            def __init__(self, segments_path, debug):
                self.type = 'wvtt'
                self.init_path = os.path.join(segments_path, 'init.mp4')
                self.segments_path = segments_path
                self.debug = debug
                self.segment_time = 0
        args = Attr(segments_path, debug)
        parse(args)

    def get_time_scale(self, mpd_url, headers):
        res = requests.get(url=mpd_url, headers=headers)
        if res.ok:
            timescale = re.search(r'(?<=timescale=\")\d*(?=\")', res.text)
            return float(timescale.group())
        else:
            self.logger.error(res.text)

    def rename_file_name(self, filename):

        filename = (
            filename.replace(" ", ".")
            .replace("'", "")
            .replace('"', "")
            .replace(",", "")
            .replace("-", "")
            .replace(":", "")
            .replace("’", "")
            .replace('"', '')
            .replace("-.", ".")
            .replace(".-.", ".")
        )
        filename = re.sub(" +", ".", filename)
        for i in range(10):
            filename = re.sub(r"(\.\.)", ".", filename)

        return filename
