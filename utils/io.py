#!/usr/bin/python3
# coding: utf-8

"""
This module is for I/O.
"""

from __future__ import annotations
import logging
import multiprocessing
from operator import itemgetter
import os
from typing import Union
from pathlib import Path
import re
from tqdm import tqdm
import requests
import rtoml
from configs.config import user_agent
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
    for i in range(5):
        filename = re.sub(r"(\.\.)", ".", filename)
    filename = re.sub(r'[/\\:|<>"?*\0-\x1f]|^(AUX|COM[1-9]|CON|LPT[1-9]|NUL|PRN)(?![^.])|^\s|[\s.]$',
                      "", filename[:255], flags=re.IGNORECASE)

    return filename


def download_file(url, output_path, headers={}):
    """Download file from url"""

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
        ) as bar:
            for data in res.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    else:
        logger.warning(_("\nFile not found!"))


def download_files(files, headers={}):
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
                file_name = os.path.join(file['path'], file['name'].replace(
                    extension, f'-seg_{sequence}{extension}'))
                lang_paths.append(file['path'])
            else:
                file_name = os.path.join(file['path'], file['name'])
            pool.apply_async(download_file, args=(
                file['url'], file_name, headers))
    pool.close()
    pool.join()


def download_audio(m3u8_url, output):
    """Download audios from m3u8 url"""

    os.system(
        f'ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "{m3u8_url}" -c copy "{output}" -preset ultrafast -loglevel warning -hide_banner -stats')


if __name__:
    logger = logging.getLogger(__name__)
    _ = get_locale(__name__)
