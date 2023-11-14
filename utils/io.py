#!/usr/bin/python3
# coding: utf-8

"""
This module is for I/O.
"""

from __future__ import annotations
import logging
import multiprocessing
import os
import re
import sys
from operator import itemgetter
from pathlib import Path
from typing import Union
from urllib.parse import quote

from tqdm import tqdm
import requests
import rtoml
from configs.config import user_agent, credentials
from utils.helper import check_url_exist, get_locale


def load_toml(path: Union[Path, str]) -> dict:
    """Read .toml file"""

    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_file():
        return {}
    return rtoml.load(path)


def rename_filename(filename):
    """Fix invalid character from title"""

    filename = (
        filename.replace(" ", ".")
        .replace("'", "")
        .replace('"', "")
        .replace(",", "")
        .replace("-", "")
        .replace(":", ".")
        .replace("’", "")
        .replace('"', '')
        .replace("-.", ".")
        .replace(".-.", ".")
    )
    filename = re.sub(" +", ".", filename)
    for _ in range(5):
        filename = re.sub(r"(\.\.)", ".", filename)
    filename = re.sub(r'[/\\:|<>"?*\0-\x1f]|^(AUX|COM[1-9]|CON|LPT[1-9]|NUL|PRN)(?![^.])|^\s|[\s.]$',
                      "", filename[:255], flags=re.IGNORECASE)

    return filename


def get_tmdb_info(title: str, release_year: str = "", is_movie: bool = False) -> dict:
    """Get tmdb information."""
    api_key = credentials['TMDB']['api_key']

    if not api_key:
        logger.error(
            "Please get tmdb api key and set in video_downloader.toml!")
        sys.exit(1)

    url = f"https://api.themoviedb.org/3/search/{'movie' if is_movie else 'tv'}?query={quote(title)}"

    if release_year:
        url += f"&{'primary_release_year' if is_movie else 'first_air_date_year'}={release_year}"

    url += f"&api_key={api_key}"

    res = requests.get(
        url, headers={'User-Agent': user_agent}, timeout=1)
    if res.ok:
        return res.json()
    else:
        logger.error(res.text)
        sys.exit(1)


def download_file(url, output_path, headers=None):
    """Download file from url and show progress"""

    if check_url_exist(url):

        if not headers:
            headers = {'User-Agent': user_agent}

        res = requests.get(url, headers=headers, stream=True, timeout=10)
        total = int(res.headers.get('content-length', 0))
        with open(output_path, 'wb') as file, tqdm(
            desc=os.path.basename(output_path),
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as progress_bar:
            for data in res.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)

    else:
        logger.warning(_("\nFile not found!"))


def download_files(files, headers=None):
    """Multi-processing download files"""

    cpus = multiprocessing.cpu_count()
    max_pool_size = 8
    pool = multiprocessing.Pool(
        cpus if cpus < max_pool_size else max_pool_size)

    lang_paths = []
    for file in sorted(files, key=itemgetter('name')):
        if 'url' in file and 'name' in file and 'path' in file:
            if 'segment' in file and file['segment']:
                extension = Path(file['name']).suffix
                sequence = str(lang_paths.count(file['path'])).zfill(3)
                if file['segment'] == 'comment':
                    filename = os.path.join(file['path'], file['name'].replace(
                        extension, f'-seg_{sequence}_comment{extension}'))
                else:
                    filename = os.path.join(file['path'], file['name'].replace(
                        extension, f'-seg_{sequence}{extension}'))
                lang_paths.append(file['path'])
            else:
                filename = os.path.join(file['path'], file['name'])
            pool.apply_async(download_file, args=(
                file['url'], filename, headers))
    pool.close()
    pool.join()


def download_audio(m3u8_url, output):
    """Download audios from m3u8 url"""

    os.system(
        f'ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "{m3u8_url}" -c copy "{output}" -preset ultrafast -loglevel warning -hide_banner -stats')


if __name__:
    logger = logging.getLogger(__name__)
    _ = get_locale(__name__)
