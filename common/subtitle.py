#!/usr/bin/python3
# coding: utf-8

"""
This module is to handle subtitle.
"""
import re
import logging
import os
import shutil
from pathlib import Path
import pysubs2
from chardet import detect
from common.utils import get_locale


def get_encoding_type(source):
    """
    Get file encoding type
    """
    with open(source, 'rb') as source:
        rawdata = source.read()
    return detect(rawdata)['encoding']


def convert_utf8(srcfile):
    """
    Convert file to utf8
    """

    from_codec = get_encoding_type(srcfile)
    try:
        if from_codec.lower() != 'utf-8':
            if from_codec == 'BIG5' or from_codec == 'GBK' or from_codec == 'GB2312' or from_codec == 'Windows-1252' or from_codec == 'ISO-8859-1':
                from_codec = 'CP950'

            with open(srcfile, 'r', encoding=from_codec, errors='replace') as input_src:
                data = input_src.read()
            with open(srcfile, 'w', encoding='UTF-8') as output_src:
                output_src.write(data)

    except UnicodeDecodeError:
        logger.error("Decode Error")
    except UnicodeEncodeError:
        logger.error("Encode Error")


def convert_subtitle(folder_path="", ott="", lang=""):
    """
    Convert subtitle to .srt
    """

    _ = get_locale(__name__, lang)
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            display = True
            for file in sorted(os.listdir(folder_path)):
                extenison = Path(file).suffix
                if os.path.isfile(os.path.join(folder_path, file)) and extenison != '.srt':
                    if display:
                        logger.info(
                            _("\nConvert %s to .srt:\n---------------------------------------------------------------"), extenison)
                        display = False
                    subtitle = os.path.join(folder_path, file)
                    subtitle_name = subtitle.replace(
                        Path(subtitle).suffix, '.srt')
                    convert_utf8(subtitle)
                    subs = pysubs2.load(subtitle)
                    subs = format_subtitle(subs)
                    subs.save(subtitle_name)
                    os.remove(subtitle)
                    logger.info(os.path.basename(subtitle_name))
            if ott:
                archive_subtitle(path=os.path.normpath(
                    folder_path), ott=ott, lang=lang)
        else:
            subtitle_name = folder_path.replace(
                Path(folder_path).suffix, '.srt')
            convert_utf8(folder_path)
            subs = pysubs2.load(folder_path)
            subs = format_subtitle(subs)
            subs.save(subtitle_name)
            os.remove(folder_path)
            logger.info(os.path.basename(subtitle_name))


def archive_subtitle(path, ott="", lang=""):
    """
    Archive subtitles
    """
    _ = get_locale(__name__, lang)
    logger.info(
        _("\nArchive subtitles:\n---------------------------------------------------------------"))

    if ott:
        zipname = os.path.basename(f'{path}.WEB-DL.{ott}')
    else:
        zipname = os.path.basename(f'{path}.WEB-DL')

    zipname = os.path.normpath(zipname)
    path = os.path.normpath(path)
    logger.info('%s.zip', zipname)

    shutil.make_archive(zipname, 'zip', path)

    if str(os.getcwd()) != str(Path(path).parent.absolute()):
        exist_zip = os.path.join(
            Path(path).parent.absolute(), f'{os.path.basename(zipname)}.zip')
        if os.path.exists(exist_zip):
            os.remove(exist_zip)
        shutil.move(f'{zipname}.zip', Path(path).parent.absolute())


def ms_to_timestamp(ms: int) -> str:
    """Convert ms to 'HH:MM:SS,mmm'"""
    MAX_REPRESENTABLE_TIME = 359999999

    if ms < 0:
        ms = 0
    if ms > MAX_REPRESENTABLE_TIME:
        ms = MAX_REPRESENTABLE_TIME
    h, m, s, ms = pysubs2.time.ms_to_times(ms)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def convert_list_to_subtitle(subs):
    """
    Convert list to subtitle
    """
    text = ''
    for index, sub in enumerate(subs):

        text = text + str(index + 1) + '\n'
        text = text + ms_to_timestamp(sub.start) + \
            ' --> ' + ms_to_timestamp(sub.end) + '\n'
        text = text + \
            sub.text.replace('\\n', '\n').replace('\\N', '\n').strip()
        text = text + '\n\n'

    return pysubs2.ssafile.SSAFile.from_string(text)


def merge_subtitle_fragments(folder_path="", file_name="", lang="", display=False):
    """
    Merge subtitle fragments
    """
    _ = get_locale(__name__, lang)
    if os.path.exists(folder_path):
        if display:
            logger.info(_(
                "\nMerge segments：\n---------------------------------------------------------------"))
        subtitles = []
        for segment in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, segment)
            subs = pysubs2.load(file_path)
            subtitles += subs
        subs = convert_list_to_subtitle(subtitles)
        file_path = os.path.join(
            Path(folder_path).parent.absolute(), file_name)
        subs.sort()
        subs = format_subtitle(subs)
        subs.save(file_path)
        logger.info(file_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)


def format_subtitle(subs):
    """
    Format subtitle
    """
    for sub in subs:
        text = sub.text
        if re.search(r'[\u4E00-\u9FFF]', text):
            text = text.replace('(', '（')
            text = text.replace(')', '）')
            text = text.replace('!', '！')
            text = text.replace('?', '？')
            text = text.replace(':', '：')
            text = text.replace('...', '…')
            text = text.replace(' （', '（')
            text = text.replace('） ', '）')

            if text.count('-') == 2:
                text = text.replace('- ', '-')

            text = re.sub(r',([\u4E00-\u9FFF]+)', '，\\1', text)
            text = re.sub(r'([\u4E00-\u9FFF]+),', '\\1，', text)

        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')

        sub.text = text.strip()

    return subs


if __name__:
    logger = logging.getLogger(__name__)
