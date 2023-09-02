#!/usr/bin/python3
# coding: utf-8

"""
This module is to handle subtitle.
"""
import glob
import re
import logging
import os
import shutil
from pathlib import Path
import sys
import pysubs2
from chardet import detect
from utils.helper import get_locale
from constants import SUBTITLE_FORMAT


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
        if from_codec and from_codec.lower() != 'utf-8':
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


def is_subtitle(file_path, file_format=''):
    """
    Check subtitle is in valid format
    """

    extenison = Path(file_path).suffix.lower()
    if os.path.isfile(file_path) and Path(file_path).stat().st_size > 0 and extenison in SUBTITLE_FORMAT:
        if file_format and file_format != extenison:
            return False
        return True


def set_ass_style(subs):
    """
    Set .ass style
    """
    style = subs.styles["Default"].copy()
    style.fontname = 'Lucida Grande'
    style.fontsize = 28
    style.backcolor = pysubs2.Color(0, 0, 0, 80)
    style.bold = 0
    style.outline = 0.8
    style.shadow = 0.5

    subs.styles['Default'] = style

    comment_name = 'Comment'
    comment = style.copy()
    subs.styles[comment_name] = comment

    for sub in subs:
        text = sub.text
        text = re.sub(r"\n", r"\\N", text)
        if '{\\an8}' in text:
            sub.name = comment_name
        sub.text = text.strip()
    return subs


def convert_subtitle(folder_path="", platform="", subtitle_format="", locale=""):
    """
    Convert subtitle to .srt or .ass
    """
    _ = get_locale(__name__, locale)

    if not subtitle_format:
        subtitle_format = '.srt'

    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            display = True
            folder = os.listdir(folder_path)
            for file in sorted(folder):
                extenison = Path(file).suffix.lower()
                if is_subtitle(os.path.join(folder_path, file), '.vtt'):
                    if display:
                        logger.info(
                            _("\nConvert %s to %s:\n---------------------------------------------------------------"), extenison, subtitle_format)
                        display = False

                    subtitle = os.path.join(folder_path, file)
                    subtitle_name = subtitle.replace(
                        extenison, subtitle_format)
                    convert_utf8(subtitle)
                    subs = pysubs2.load(subtitle)
                    if '.zh-Hant' in subtitle_name:
                        subs = format_zh_subtitle(subs)
                    subs = format_subtitle(subs)
                    if subtitle_format == '.ass':
                        subs = set_ass_style(subs)
                    subs.save(subtitle_name)
                    logger.info(os.path.basename(subtitle_name))
                    os.remove(subtitle)
                    folder = os.listdir(folder_path)
            if platform:
                archive_subtitle(folder_path=os.path.normpath(
                    folder_path), platform=platform, locale=locale)

        elif is_subtitle(folder_path, '.vtt'):
            subtitle_name = folder_path.replace(
                Path(folder_path).suffix, subtitle_format)
            convert_utf8(folder_path)
            subs = pysubs2.load(folder_path)
            if '.zh-Hant' in subtitle_name:
                subs = format_zh_subtitle(subs)
            subs = format_subtitle(subs)
            if subtitle_format == '.ass':
                subs = set_ass_style(subs)
            subs.save(subtitle_name)
            os.remove(folder_path)
            logger.info(os.path.basename(subtitle_name))


def archive_subtitle(folder_path, platform="", locale=""):
    """
    Archive subtitles
    """
    _ = get_locale(__name__, locale)

    contain_subtitle = False
    for path, dirs, files in os.walk(folder_path):
        if any('.srt' in s for s in files):
            contain_subtitle = True
            break

    if not contain_subtitle:
        sys.exit(0)

    logger.info(
        _("\nArchive subtitles:\n---------------------------------------------------------------"))

    if platform:
        zipname = os.path.basename(f'{folder_path}.WEB-DL.{platform}')
    else:
        zipname = os.path.basename(f'{folder_path}.WEB-DL')

    folder_path = os.path.normpath(folder_path)
    logger.info("%s.zip", zipname)

    shutil.make_archive(Path(folder_path).parent / zipname, 'zip', folder_path)


def ms_to_timestamp(ms: int) -> str:
    """
    Convert ms to 'HH:MM:SS,mmm'
    """
    max_representable_time = 359999999

    if ms < 0:
        ms = 0
    if ms > max_representable_time:
        ms = max_representable_time
    return "%02d:%02d:%02d,%03d" % (pysubs2.time.ms_to_times(ms))


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


def merge_same_subtitle(subs):
    """
    Merge same subtitles
    """
    for i, sub in enumerate(subs):
        if i > 0 and sub.text == subs[i-1].text and sub.start - subs[i-1].end <= 20:
            subs[i-1].end = sub.end
            subs.pop(i)
        elif sub.text == '':
            subs.pop(i)
    return subs


def merge_subtitle_fragments(folder_path="", filename="", subtitle_format="", locale="", display=False, shift_time=None):
    """
    Merge subtitle fragments
    """
    _ = get_locale(__name__, locale)

    if not subtitle_format:
        subtitle_format = '.srt'

    if os.path.exists(folder_path) and glob.glob(os.path.join(folder_path, '*.srt')) + glob.glob(os.path.join(folder_path, '*.vtt')):
        if display:
            logger.info(_(
                "\nMerge segments：\n---------------------------------------------------------------"))
        subtitles = []
        for segment in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, segment)
            if is_subtitle(file_path):
                subs = pysubs2.load(file_path)
                if shift_time:
                    offset = next(
                        (seg['offset'] for seg in shift_time if seg['name'] in file_path), '')
                    subs.shift(s=offset)
                subs = clean_subs(subs)
                if 'comment' in file_path:
                    add_comment(subs)
                subtitles += subs
        subs = convert_list_to_subtitle(subtitles)
        subs = merge_same_subtitle(subs)
        file_path = os.path.join(
            Path(folder_path).parent.absolute(), filename)
        subs.sort()
        if '.zh-Hant' in file_path or '.cmn-Hant' in file_path:
            subs = format_zh_subtitle(subs)
        subs = format_subtitle(subs)
        extenison = Path(file_path).suffix.lower()
        file_path = file_path.replace(extenison, subtitle_format)
        if subtitle_format == '.ass':
            subs = set_ass_style(subs)
        subs.save(file_path)
        logger.info(os.path.basename(file_path))
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)


def add_comment(subs):
    """
    Add comment to subtitle
    """
    for sub in subs:
        sub.text = '{\\an8}' + sub.text.strip()
    return subs


def format_zh_subtitle(subs):
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
            text = text.replace('） ', '）')
            text = text.replace('） ', '）')

            if text.count('-') == 2:
                text = text.replace('- ', '-')

            text = re.sub(r',([\u4E00-\u9FFF]+)', '，\\1', text)
            text = re.sub(r'([\u4E00-\u9FFF]+),', '\\1，', text)

            text = re.sub(r'\u3000\u3000', ' -', text)

            conversation = re.search(r'( )-[ \u4E00-\u9FFF「0-9]+', text)
            if conversation:
                text = text.replace(' -', '\n-')

            text = re.sub(r'(^[「\u4E00-\u9FFF]+.*?)\n-', '-\\1\n-', text)

        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')

        sub.text = text.strip()

    return subs


def clean_subs(subs):
    """
    Clean redundant subtitles
    """
    for sub in subs:
        text = sub.text
        text = re.sub(r"&rlm;", "", text)
        text = re.sub(r"&lrm;", "", text)
        text = re.sub(r"&amp;", "&", text)
        sub.text = text.strip()
    return subs


def format_subtitle(subs):
    """
    Format subtitle
    """
    delete_list = []
    for i, sub in enumerate(subs):
        sub.text = re.sub(r'\u200b', '', sub.text)
        sub.text = re.sub(r'\u200e', '', sub.text)
        sub.text = re.sub(r'\u202a', '', sub.text)
        sub.text = re.sub(r'\ufeff', '', sub.text)
        sub.text = re.sub(r'\xa0', ' ', sub.text)

        if sub.text == "":
            delete_list.append(i)

    for i in reversed(delete_list):
        del subs[i]

    return subs


if __name__:
    logger = logging.getLogger(__name__)
