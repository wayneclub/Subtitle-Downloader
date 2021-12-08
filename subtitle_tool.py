# -*- coding: UTF-8 -*-

"""
Fix subtitles srt
"""
import shutil
import time
import argparse
import sys
import io
import os
from pathlib import Path
import re
import unicodedata
import pysubs2
from common.dictionary import translate
import difflib
from chardet import detect
from bs4 import BeautifulSoup, CData
import json
import opencc
import zipfile
import subprocess

SUBTITLE_FORMAT = ['.srt', '.ass', '.ssa', '.vtt', '.xml', '.json']
IMAGE_FORMAT = ['.bmp', '.png', '.jpg', '.jpeg', '.tif', '.tiff']
ARCHIVE_FORMAT = ['.7z', '.gz', '.rar', '.tar', '.zip']


def get_encoding_type(source):
    """
    Get file encoding type
    """
    with open(source, 'rb') as source:
        rawdata = source.read()
    return detect(rawdata)['encoding']


def subtitle_format(sub_format):
    """
    Check subtitle format
    """
    if sub_format != '.srt' and sub_format != '.ass':
        raise argparse.ArgumentTypeError("只支持將字幕轉換成 .srt 或 .ass\n")
    return sub_format


def get_line_width(line):
    """
    Determines the width of the line in column positions.
    Args:
        line: A string, which may be a Unicode string.
    Returns:
        The width of the line in column positions, accounting for Unicode
        combining characters and wide characters.
    """
    if isinstance(line, str):
        width = 0
        for unicode in unicodedata.normalize('NFC', line):
            if unicodedata.east_asian_width(unicode) in ('W', 'F'):
                width += 2
            elif not unicodedata.combining(unicode):
                width += 1
        return width
    else:
        return len(line)


def convert_utf8(srcfile):
    """
    Convert file to utf8
    """

    from_codec = get_encoding_type(srcfile)
    try:
        if from_codec.lower() != 'utf-8':
            if from_codec == 'BIG5' or from_codec == 'GB2312' or from_codec == 'Windows-1252' or from_codec == 'ISO-8859-1':
                from_codec = 'CP950'

            print("\n將" + from_codec +
                  " 轉換成 UTF-8：\n---------------------------------------------------------------")

            with open(srcfile, 'r', encoding=from_codec, errors='replace') as input_src:
                data = input_src.read()
            with open(srcfile, 'w', encoding='UTF-8') as output_src:
                output_src.write(data)

            print(srcfile)

    except UnicodeDecodeError:
        print("Decode Error")
    except UnicodeEncodeError:
        print("Encode Error")


def convert_list_to_subtitle(subs):
    """
    Convert list to subtitle
    """
    text = ''
    for index, sub in enumerate(subs):
        # if index != 0:
        #     file.write('\n\n')

        text = text + str(index + 1) + '\n'
        text = text + str(pysubs2.subrip.ms_to_timestamp(sub.start)) + \
            ' --> ' + str(pysubs2.subrip.ms_to_timestamp(sub.end)) + '\n'
        text = text + \
            sub.text.replace('\\n', '\n').replace('\\N', '\n').strip()
        text = text + '\n\n'

    return pysubs2.ssafile.SSAFile.from_string(text)


def shift_subtitle(file_name, offset, start):
    """
    Shift subtitle
    """
    subs = pysubs2.load(file_name)
    if start:
        print('\n字幕從' + start + '開始平移：' + str(offset) + ' 秒\n')
        start_time = pysubs2.subrip.timestamp_to_ms(start)
        for sub in subs:
            if sub.start >= start_time:
                sub.start = sub.start + offset * 1000
                sub.end = sub.end + offset * 1000
    else:
        print('\n字幕平移：' + str(offset) + ' 秒\n')
        subs.shift(s=offset)

    subs.save(file_name)
    print(file_name)


def change_subtitle_fps(file_name, frame_rate):
    """
    Change Subtitle FPS
    """
    subs = pysubs2.load(file_name)
    subs.transform_framerate(25, 23.976)
    # make_time(frames=50, fps=25)
    subs.save(file_name)
    # print(file_name)


def merge_subtitle(first_file, second_file):
    """
    Merge subtitle
    """

    audio_lang = 'ko'

    subs_first = pysubs2.load(first_file)
    subs_first.sort()
    subs_second = pysubs2.load(second_file)
    subs_second.sort()

    episode = re.search(r'(.+?S\d+E)(\d+)(.*?\.srt)', first_file)
    if episode:
        new_file_name = episode.group(
            1) + episode.group(2).zfill(2) + '-E' + str(int(episode.group(2))+1).zfill(2) + '.srt'
    else:
        new_file_name = first_file.replace('.srt', '-merge.srt')

    delta = 5

    if subs_second[0].start < subs_first[-1].end:
        offset = subs_first[-1].end/1000 + delta
        if offset < 30*60:
            offset = 1800
    else:
        offset = 0

    for sub in subs_second:
        if sub.text[0] != '（':
            closest_second_sub_first = sub.start
            break

    video = ''

    if os.path.exists(new_file_name.replace('.zh', '').replace('.srt', '.mkv')):
        video = new_file_name.replace('.zh', '').replace('.srt', '.mkv')
    elif os.path.exists(new_file_name.replace('.zh', '').replace('.srt', '.mp4')):
        video = new_file_name.replace('.zh', '').replace('.srt', '.mp4')

    if video:
        print('\n根據「' + os.path.basename(video) +
              '」校正字幕時間軸：\n---------------------------------------------------------------')
        audio_info_command = "mkvmerge -i \'" + video + "'"
        audio_info_result = re.search(r'Track ID ([0-9]): audio \((.+?)\)',
                                      subprocess.getoutput(audio_info_command))
        if audio_info_result:
            audio_track = audio_info_result.group(1)
            audio_extension = '.' + audio_info_result.group(2).lower()
            audio = video.replace(Path(
                video).suffix, '_tmp' + audio_extension)
            tmp_file = audio.replace(audio_extension, '.srt')

            if not os.path.exists(audio):
                print(
                    '\n擷取影片音檔：\n---------------------------------------------------------------')
                extract_audio_command = "mkvextract tracks '" + \
                    video + "' " + audio_track + ":'" + audio + "'"
                if re.search(r'Progress: 100%', subprocess.getoutput(extract_audio_command)):
                    print(os.path.basename(audio))

            if not os.path.exists(tmp_file):
                print(
                    '\n將音檔轉成.srt：\n---------------------------------------------------------------')
                audio_to_srt_command = "autosub -S " + audio_lang + \
                    " -D " + audio_lang + " '" + audio + "'"
                srt_result = re.search(
                    r'Subtitles file created at (.+)', subprocess.getoutput(audio_to_srt_command))
                if srt_result:
                    tmp_file = srt_result.group(1)
                    print(tmp_file)
                    os.remove(audio)

            subs_tmp = pysubs2.load(tmp_file)

            for index, sub in enumerate(subs_tmp):
                if pysubs2.subrip.ms_to_timestamp(subs_first[-1].end)[:-4] in pysubs2.subrip.ms_to_timestamp(sub.end)[:-4]:
                    if 0 < index < len(subs_tmp) and closest_second_sub_first:
                        offset = (subs_tmp[index+1].start -
                                  closest_second_sub_first)/1000
                        break

    print('\n字幕平移：' + str(offset) + ' 秒\n')
    subs_second.shift(s=offset)

    print('\n合併字幕：' + os.path.basename(first_file) + ' 和 ' + os.path.basename(second_file) +
          '\n---------------------------------------------------------------')

    for sub in subs_second:
        subs_first.append(sub)

    subs_first.sort()

    subs_first.save(new_file_name)
    print(os.path.basename(new_file_name) + '\t...合併完成\n')


def format_subtitle(file_name):
    """
    Format subtitle
    """
    subs = pysubs2.load(file_name)

    delete_list = []
    for i, sub in enumerate(subs):
        if sub.text == "":
            delete_list.append(i)

    for i in reversed(delete_list):
        del subs[i]

    subs.save(file_name)


def translate_subtitle(file_name, language, remove_cast):
    """
    Uniform punctuation and translate term to Traditional Chinese
    """

    if language == 's':
        print("簡體轉繁體：---------------------------------------------------------------")
        os.system('OpenCC -i "' + file_name + '" -o "' +
                  file_name + '" -c "s2tw.json"')

    subs = pysubs2.load(file_name)

    path = file_name.split(os.path.basename(file_name))[0]
    new_file_name = rename_subtitle(file_name)
    new_file_name = re.sub(r'(-|\.)ch[st]+', '', new_file_name, flags=re.I)
    new_file_name = re.sub(r'-AREA11', '', new_file_name)
    new_file_name = re.sub(
        r'(.+?)(\.)*[sS]([0-9]{2})[eE]([0-9]{2,3})(-([eE])*[0-9]{2,3})*.+',
        '\\1.S\\3E\\4\\5.srt',
        new_file_name)

    original_line_num = len(subs)
    delete_list = []
    typo_compare_list = []

    for i, sub in enumerate(subs):
        text = sub.text.strip()

        text = text.replace('\\N', '\n')
        text = text.replace('/N', '\n')
        text = text.replace('\\n', '\n')

        if not text or text == '' or text == '\n':
            delete_list.append(i)
            continue

        if sub.start == sub.end:
            delete_list.append(i)
            continue

        # remove lyrics
        # if text[0] == '♫':
        #     delete_list.append(i)
        #     continue

        if text[0] == '©' or text[0] == 'ⓒ':
            delete_list.append(i)
            print(
                "\n刪除字幕：\n---------------------------------------------------------------")
            print(text)
            continue

        if text == '切':
            delete_list.append(i)
            print(
                "\n刪除字幕：\n---------------------------------------------------------------")
            print(text)
            continue

        if '本節目包含置入性廣告與插播廣告' in text or 'NETFLIX 出品' in text or 'NETFLIX 系列' in text or 'NETFLIX 影集' in text or 'NETFLIX 原創影集' in text or 'NETFLIX 原創電影' in text or '字幕翻譯' in text:
            print(
                "\n刪除字幕：\n---------------------------------------------------------------")
            print(text)
            delete_list.append(i)
            continue

        if re.search(r'\{\\.*?(pos|fad)\([0-9\.]+,[0-9\.]+\).*?\}', text):
            text = '（' + re.sub(r'(\{.+?\})+', '', text) + '）'

        if re.search(r'\{.*?\\an8.*?\}', text):
            if '（' not in text:
                text = '（' + re.sub(r'(\{.+?\})+', '', text) + '）'
            else:
                text = re.sub(r'(\{.+?\})+', '', text)
        elif re.search(r'\{\\.+?\}', text):
            text = re.sub(r'(\{.+?\})+', '', text)

        text = re.sub(r',([\u4E00-\u9FFF]+)', ' \\1', text)
        text = re.sub(r'([\u4E00-\u9FFF]+),', '\\1', text)

        text = re.sub(r'([\u4E00-\u9FFF]+)\[', '\\1 [', text)
        text = re.sub(r'\]([\u4E00-\u9FFF]+)', '] \\1', text)

        text = re.sub(r'\u200e', '', text)
        text = re.sub(r'\u202a', '', text)
        text = re.sub(r'\xa0', ' ', text)
        # if text[0] == '「' and text[-1] == '」':
        #     text = '（' + text[1:len(text)-1] + '）'

        text = text.replace('　', ' ')
        text = text.replace('', ' ')
        text = text.replace('\t', ' ')

        # Uniform and fix punctuation errors
        text = text.replace('`', '')
        text = text.replace('ˊ', '')
        text = text.replace('∕', '/')
        text = text.replace('＂', '"')
        text = text.replace('➚', '')
        text = text.replace('...', '…')
        text = text.replace('⋯', '…')
        text = text.replace(',,,', '…')
        text = text.replace('..,', '…')
        text = text.replace('.,.', '…')
        text = text.replace('..', '…')
        text = text.replace('‥', '…')
        text = text.replace('．．．', '…')
        text = text.replace('﹒﹒﹒', '…')
        text = text.replace('。。。', '…')
        text = text.replace(' …', '…')
        text = text.replace('….', '…')
        text = text.replace('……', '…')
        text = text.replace('・・・', '…')
        text = text.replace('!?', '！？')
        text = text.replace('⁉︎', '！？')
        text = text.replace('?!', '！？')
        text = text.replace('？!', '！？')
        text = text.replace('!', '！')
        text = text.replace('?', '？')
        text = text.replace('！', '！')
        text = text.replace('﹗', '！')
        text = text.replace('？', '？')
        text = text.replace(' ！', '！')
        text = text.replace(' ？', '？')
        text = text.replace('？ ？', '？？')
        text = text.replace('！！', '！')
        text = text.replace('！！', '！')
        text = text.replace('！！！', '！')
        text = text.replace('﹐', '，')
        text = text.replace('。', ' ')
        text = text.replace('﹑', '、')
        text = text.replace('、 ', '、')
        text = text.replace(' 、', '、')
        text = text.replace('╱', '／')
        text = text.replace('／', '/')
        text = text.replace(',\n\r', '')
        text = text.replace(':', '：')
        text = text.replace('： ', '：')
        text = text.replace('︰', '：')
        text = text.replace('：\n', '：')
        text = text.replace('~', '～')
        text = text.replace('∼', '～')
        text = text.replace('│', ' ')
        text = text.replace('|', ' ')
        text = text.replace(' |', ' ')
        text = text.replace('| ', ' ')
        text = re.sub(r'([\u4E00-\u9FFF]+)\.', '\\1 ', text)
        text = text.replace('（-= ', '（')
        text = text.replace('（-=', '（')
        text = text.replace('(', '（')
        text = text.replace('﹙', '（')
        text = text.replace('[', '（')
        text = text.replace('［', '（')
        text = text.replace('-=', '（')
        text = text.replace('-= ', '（')
        text = text.replace('-＝', '（')
        text = text.replace('【', '（')
        text = text.replace('〔', '（')
        text = text.replace(' （', '（')
        text = text.replace('（\n\r', '（')
        text = text.replace('（ ', '（')
        text = text.replace(' =-）', '）')
        text = text.replace('=-）', '）')
        text = text.replace(' =-', '）')
        text = text.replace('=-', '）')
        text = text.replace('＝-', '）')
        text = text.replace(' ）', '）')
        text = text.replace('﹚', '）')
        text = text.replace(')', '）')
        text = text.replace(']', '）')
        text = text.replace('］', '）')
        text = text.replace('】', '）')
        text = text.replace('〕', '）')
        text = text.replace('） ', '）')
        text = text.replace('\n\r)', '）')
        text = text.replace(r'\h', '')
        text = text.replace('•', '・')
        text = text.replace('‧', '・')
        text = text.replace('·', '・')
        text = text.replace('．', '・')
        text = text.replace('＄', '$')
        text = text.replace('＃', '#')
        text = text.replace('〝', '「')
        text = text.replace('〞', '」')
        text = text.replace('〟', '」')
        text = text.replace('『', '「')
        text = text.replace('』', '」')
        text = text.replace('“', '「')
        text = text.replace('”', '」')
        text = text.replace('「', '「')
        text = text.replace(' 」', '」')
        text = text.replace('｣', '」')
        text = text.replace('」…', '…」')
        text = text.replace('注：', '註：')
        text = text.replace('（註：', '\n（註：')
        text = text.replace('->', ' → ')
        text = text.replace('<-', ' ← ')
        text = text.replace('〈', '（')
        text = text.replace('〉', '）')
        text = re.sub(r'^[<＜]', '（', text)
        text = re.sub(r'[>＞]$', '）', text)
        text = text.replace('‐', '-')
        text = text.replace('－', '-')
        text = text.replace('﹣', '-')
        text = text.replace('–', '-')
        text = text.replace('ー', '-')
        text = text.replace('- ', '-')
        text = text.replace('“', '"')
        text = text.replace('”', '"')
        text = text.replace('’', "'")
        text = text.replace('‘', "'")
        text = text.replace('％', "%")

        if text[0] == '…':
            text = text[1:] + '…'
            text = text.replace('……', '…')
            text = text.replace('！…', '！')
            text = text.replace('？…', '？')

        text = re.sub(r"^=(.+)=$", r"（\1）", text, re.S)

        text = re.sub(r"^\[(.+)\]$", r"（\1）", text, re.S)

        # 刪除換行前空白
        text = re.sub(r'\n[ ]*(.+)', '\n\\1', text)

        text = '\n'.join(filter(None, text.split('\n')))

        text = re.sub(r'([A|P]M)([0-9]{2})：([0-9]{2})', '\\2:\\3 \\1 ', text)
        text = re.sub(r'([A|P]M) ([0-9]{2})：([0-9]{2})', '\\2:\\3 \\1 ', text)
        text = re.sub(r'([0-9]+)：([0-9]+)：([0-9]+)', '\\1:\\2:\\3', text)
        text = re.sub(r'([0-9]+)：([0-9]+)', '\\1:\\2', text)

        if '-' not in text:
            if len(re.findall(r'^[\u4E00-\u9FFF]\n', text)) > 2 \
                    or len(re.findall(r'（[\u4E00-\u9FFF]\n', text)) > 2:
                text = text.replace('\n', '')

        # if re.search(r'(.+?)\n（', text):
        #     tmp_text = text.split('（', 1)
        #     text = '（' + tmp_text[1].strip() + '\n' + tmp_text[0].strip()

        text = re.sub(r'([\u4E00-\u9FFF])\.', '\\1 ', text)

        if re.search(r'[\u4E00-\u9FFF]', text) and '"' in text and text.count('"') > 1:
            count = 0
            for char in text:
                if char == '"':
                    count += 1
                    if count % 2 == 0:
                        text = text.replace('"', "」", 1)
                    else:
                        text = text.replace('"', "「", 1)
        elif re.search(r'[\u4E00-\u9FFF]', text) and text.count('"') == 1:
            if text[0] == '"':
                text = text.replace('"', '「')
            elif text[-1] == '"':
                text = text.replace('"', '」')

            text = text.replace(' "', ' 「')
            text = text.replace('" ', '」 ')
            text = re.sub(
                r'([\u4E00-\u9FFFa-zA-Z0-9])\"([\u4E00-\u9FFFa-zA-Z0-9])', '\\1「\\2', text)

        if re.search(r'「「', text) and text.count('「') - text.count('」') != 0:
            text = text.replace('「「', '「')
        elif re.search(r'」」', text) and text.count('「') - text.count('」') != 0:
            text = text.replace('」」', '」')

        if text.count('「') == 2 and text.count('」') == 0:
            text = '」'.join(text.rsplit('「', 1))
        elif text.count('」') == 2 and text.count('「') == 0:
            text = '「'.join(text.rsplit('」', 1))

        if text[0] == '」' and text.count('「') - text.count('」') != 0:
            text = text[1:] + '」'

        if re.search(r'^-」', text):
            text = '-' + text[2:] + '」'

        text = re.sub(r'([0-9]+)\.([\u4E00-\u9FFF]+)', '\\1. \\2', text)

        episode = re.search(r'（第(.*?)[集|話|回](.*?)）(.*)', text)
        if episode:
            text = '（第' + translate(episode.group(1), dictionary.NUMBER).strip() + \
                '集' + episode.group(2) + '）' + episode.group(3)

        episode = re.search(r'^第(.*?)[集|話|回]$', text)
        if episode:
            text = '（第' + \
                translate(episode.group(
                    1), dictionary.NUMBER).strip() + '集）'

        movie_name = re.search(r'^片名：(.+)', text)
        if movie_name:
            text = '（片名：' + movie_name.group(1) + '）'

        if text == '下集預告':
            text = '（下集預告）'

        if text == '下 集 預 告':
            text = '（下集預告）'

        if text == '前情提要':
            text = '（前情提要）'

        if text == '前 情 提 要':
            text = '（前情提要）'

        if text == '本集回顧':
            text = '（本集回顧）'

        if text == '本 集 回 顧':
            text = '（本集回顧）'

        conversation = re.search(r'( )-[ \u4E00-\u9FFF「0-9]+', text)
        if conversation:
            text = text.replace(' -', '\n-')

        text = re.sub(r'(^[「\u4E00-\u9FFF]+.*?)\n-', '-\\1\n-', text)

        text = text.replace('  ', ' ')
        text = text.replace('， ', '，')
        text = text.replace('！ ', '！')
        text = text.replace('？ ', '？')
        text = text.replace('…', '… ')
        text = text.replace('… ）', '…）')
        text = text.replace('-… ', '-…')
        text = text.replace('… 」', '…」')
        text = text.replace('… ！', '…！')
        text = text.replace('… ？', '…？')
        text = text.replace('\n\n', '\n')
        text = text.replace('\n ', '\n')
        text = text.replace(' \n', '\n')

        # remove cast
        if remove_cast:
            text = re.sub(r'^（片名：.+', '', text)
            text = re.sub(r'^主演：.+', '', text)
            text = re.sub(r'^製片：.+', '', text)
            text = re.sub(r'^編劇：.+', '', text)
            text = re.sub(r'^導演：.+', '', text)
            text = re.sub(r'^翻譯：.+', '', text)
            text = re.sub(r'主演：[^\n]+', '', text)
            text = re.sub(r'製片：[^\n]+', '', text)
            text = re.sub(r'編劇：[^\n]+', '', text)
            text = re.sub(r'導演：[^\n]+', '', text)
            text = re.sub(r'翻譯：[^\n]+', '', text)
            text = re.sub(r'^（MANDARIN.+', '', text)
            text = text.replace('Complexchinese', '')

        original_text = text

        # 將全形英文、數字改為半形
        text = translate(text, dictionary.SYMBOL)

        # 將香港用語轉為臺灣用語
        if language == 'hk':
            text = translate(text, dictionary.HK_TEXT)

        # 將大陸用語轉為臺灣用語
        text = translate(text, dictionary.CHS_TEXT)

        # 修正錯別字
        text = translate(text, dictionary.TYPO)

        # 去除台語
        text = translate(text, dictionary.TAIWANESE)

        sub.text = text

        # 錯字比較
        if original_text != text:
            typo_compare = {}
            typo_compare['start'] = sub.start
            typo_compare['end'] = sub.end
            typo_compare['original_text'] = original_text
            typo_compare['new_text'] = text
            typo_compare_list.append(typo_compare)

    for i in reversed(delete_list):
        del subs[i]

    delete_list = []
    for i, sub in enumerate(subs):
        text = sub.text

        if i > 0 and sub.start == subs[i-1].start and sub.end == subs[i-1].end:
            if text.replace('（', '').replace('）', '') \
                    == subs[i-1].text.replace('（', '').replace('）', ''):

                if subs[i-1].text[0] == '（':
                    delete_list.append(i)
                else:
                    delete_list.append(i-1)

            else:
                if text[0] == '（':
                    if subs[i-1].text[0] == '（':
                        if '）\n' in subs[i-1].text:
                            match = list(re.finditer(r'）\n', subs[i-1].text))
                            pos = match[-1].span()[1]
                            if match:
                                subs[i-1].text = subs[i-1].text[:pos] + \
                                    text + '\n' + subs[i-1].text[pos:]
                        else:
                            subs[i-1].text = subs[i-1].text + '\n' + text
                    else:
                        subs[i-1].text = text + '\n' + subs[i-1].text
                else:
                    subs[i-1].text = subs[i-1].text + '\n' + text
                delete_list.append(i)
        else:
            subs[i].text = text

    for i in reversed(delete_list):
        del subs[i]

    subs.sort()

    overlap_list = []
    overlength_list = []

    print("\n訂正錯字、修改成台灣慣用語：\n---------------------------------------------------------------")

    for index, sub in enumerate(subs):
        text = sub.text
        if re.search(r'（註：.+?）\n', text, flags=re.S):
            tmp = text.split('）\n')
            text = tmp[1] + '\n' + tmp[0] + '）'
        text = text.replace('  ', ' ')

        sub.text = fix_overlength(text)

        if '\n' not in sub.text and get_line_width(sub.text.replace('{\\an8}', '')) > 40:
            overlength_list.append(sub)

        if sub.text.count('\n') > 1:
            print(
                '\n行數過多：\n---------------------------------------------------------------\n' + sub.text + '\n')

        if (index > 0 and sub.start < subs[index-1].end) or (index+1 < len(subs) and sub.end > subs[index+1].start):
            overlap_list.append(sub)

        for typo_compare in typo_compare_list:
            if typo_compare['start'] == sub.start and typo_compare['end'] == sub.end:
                typo_compare.update({'index': index + 1})

        print_illegal_characters(sub)

        notice_list = ['字幕', '時間軸', '校正', '譯者', '翻譯', '導演', '編劇', '製片', '出品', 'mandarin',
                       'traditional', 'r3', 'chinese', '劇終', '謝謝觀賞', '"', '\'', '[']
        if any(part in sub.text.lower() for part in notice_list):
            print(sub.text + '\n')

        if '「' or '」' in sub.text:
            if sub.text.count('「') - sub.text.count('」') != 0:
                print(sub.text + '\n')

        if '（' or '）' in sub.text:
            if sub.text.count('（') - sub.text.count('）') != 0:
                print(sub.text + '\n')

        if re.search(r'-.+-', sub.text):
            print(sub.text + '\n')

        if re.search(r'[\u4E00-\u9FFF]-', sub.text):
            print(sub.text + '\n')

        if re.search(r'l[0-9]', sub.text):
            print(sub.text + '\n')

        if re.search(r'^…', sub.text):
            print(sub.text + '\n')

        if re.search(r'（（', sub.text) or re.search(r'））', sub.text):
            print(sub.text + '\n')

        if re.search(r'-（', sub.text):
            print(sub.text + '\n')

        if re.search(r'[\u4E00-\u9FFF]（', sub.text) or re.search(r'）[\u4E00-\u9FFF]', sub.text):
            print(sub.text + '\n')

    # 字幕重疊
    print_overlap(path + new_file_name, overlap_list)

    # 過長字幕
    print_overlength(path + new_file_name, overlength_list)

    # 錯字比較
    output_typo_compare(path + new_file_name, typo_compare_list)

    subs = merge_same_subtitle(subs)

    if '.zh' not in new_file_name:
        new_file_name = new_file_name.replace('.srt', '.zh-Hant.srt')

    print('\n' + new_file_name)

    subs.save(path + new_file_name)

    if path + new_file_name != file_name:
        os.remove(file_name)

    print('{0: <15}'.format("原始行數：" + str(original_line_num)) +
          '{0: <15}'.format("修正後行數：" + str(len(subs))) +
          '{0: <15}'.format("重疊行數：" + str(len(overlap_list))) +
          '{0: <15}'.format("過長行數：" + str(len(overlength_list))) + '\n')


def merge_same_subtitle(subs):
    delete_list = []
    for i, sub in enumerate(subs):
        if i > 0 and sub.text == subs[i-1].text and (sub.start == subs[i-1].end or sub.start - subs[i-1].end < 1000):
            delete_list.append(i)
            subs[i-1].end = sub.end
        elif sub.text == '':
            delete_list.append(i)

    for i in reversed(delete_list):
        del subs[i]
    return subs


def print_illegal_characters(sub):
    # 印出非法字幕
    illegal_character = re.findall(
        r'[^αa-zA-Z0-9\u4E00-\u9FFF!#@?\[\]\{\}&/\\,\.;:\(\)%$><=\'\"~\+\-\*_ （），。、——＋！×？：・…「」→←〈〉《》＞＜～｜\n]', sub.text)
    if len(illegal_character) > 0:
        print('\n非法字源：' + str(illegal_character) + '\n\n' + pysubs2.subrip.ms_to_timestamp(sub.start) +
              ' --> ' + pysubs2.subrip.ms_to_timestamp(sub.end) + '\n' +
              sub.text.replace('\\n', '\n') + '\n')


def print_overlap(file_name, overlap_list):
    # 印出重疊字幕

    if len(overlap_list) > 0:
        text_file = os.path.join(Path(file_name).parent, os.path.basename(
            file_name).replace(Path(file_name).suffix, '-字幕重疊.txt'))
        overlap_file = open(text_file, 'w')
        for sub in overlap_list:
            overlap_file.write(pysubs2.subrip.ms_to_timestamp(sub.start) +
                               ' --> ' + pysubs2.subrip.ms_to_timestamp(sub.end) + '\n' +
                               sub.text.replace('\\N', '\n') + '\n\n')


def print_overlength(file_name, overlength_list):
    # 印出過長字幕

    if len(overlength_list) > 0:

        text_file = os.path.join(Path(file_name).parent, os.path.basename(
            file_name).replace(Path(file_name).suffix, '-過長字幕.txt'))
        overlength_file = open(text_file, 'w')
        for sub in overlength_list:
            overlength_file.write(pysubs2.subrip.ms_to_timestamp(sub.start) +
                                  ' --> ' + pysubs2.subrip.ms_to_timestamp(sub.end) + '\n' +
                                  sub.text.replace('\\N', '\n') + '\n\n')


def fix_overlength(text):

    lines = text.split('\n')
    text = ''
    for single_line in lines:
        if get_line_width(single_line.replace('{\\an8}', '')) > 40:
            chunks = single_line.split(' ')

            str_len = 0
            size = []
            for piece in chunks:
                size.append(get_line_width(piece.replace('{\\an8}', '')))

            count = 0
            new_line = []
            for i, tmp in enumerate(size):
                if count+tmp < 40:
                    count += tmp
                else:
                    new_line.append(i)
                    count = tmp

            single_line = ''
            for x, piece in enumerate(chunks):
                if x in new_line:
                    single_line += '\n' + piece
                else:
                    if x == 0:
                        single_line += piece
                    else:
                        single_line += ' ' + piece

            text += single_line + '\n'
        else:
            text += single_line + '\n'

    return text.strip()


def output_typo_compare(file_name, typo_compare_list):
    # 印出錯字

    if len(typo_compare_list) > 0:
        text_file = os.path.join(Path(file_name).parent, os.path.basename(
            file_name).replace(Path(file_name).suffix, '-修正錯字.txt'))
        typo_compare_file = open(text_file, 'w')
        for typo_compare in typo_compare_list:
            typo_compare_file.write(str(typo_compare['index']) + '\n')
            typo_compare_file.write(pysubs2.subrip.ms_to_timestamp(
                typo_compare['start']) + ' --> ' + pysubs2.subrip.ms_to_timestamp(typo_compare['end']) + '\n')

            original_text = ''
            new_text = ''

            for i, s in enumerate(difflib.ndiff(typo_compare['original_text'].replace('\\n', '\n').replace('\\N', '\n'), typo_compare['new_text'].replace('\\n', '\n').replace('\\N', '\n'))):

                if s[0] == ' ':
                    original_text += s[2:]
                    new_text += s[2:]
                elif s[0] == '-':
                    original_text += '【' + s[-1] + '】'
                elif s[0] == '+':
                    new_text += '【' + s[-1] + '】'

            original = original_text.split('\n')
            new = new_text.split('\n')

            for i, (a, b) in enumerate(zip(original, new)):
                offset = str(40 - get_line_width(a))
                if int(offset) <= 0:
                    offset = 10

                if len(original) > 1:
                    if i == 0:
                        typo_compare_file.write(
                            f'{a:{offset}} ' + '\t---->\t' + b + '\n')
                    else:
                        typo_compare_file.write(
                            f'{a:{offset}} ' + '\t     \t' + b + '\n')
                else:
                    typo_compare_file.write(
                        f'{a:{offset}} ' + '\t---->\t' + b + '\n')

            typo_compare_file.write('\n')


def convert_subtitle(original_file, sub_type, prettify=False, print_log=True):
    extension = Path(original_file).suffix

    if not sub_type or sub_type == True:
        sub_type = '.srt'

    if sub_type != extension:
        if print_log:
            print("將" + extension +
                  " 轉換成" + sub_type + "：\n---------------------------------------------------------------")
        if sub_type == '.ass' and extension == '.srt':
            return srt_to_ass(original_file)
        else:
            if extension == '.ssa' or extension == '.ass':
                return ass_to_srt(original_file)
            elif extension == '.vtt':
                return vtt_to_srt(original_file)
            elif extension == '.xml':
                return xml_to_srt(original_file)
            elif extension == '.json':
                return json_to_srt(original_file)
    else:
        if sub_type == '.srt' and extension == '.srt':
            if prettify:
                format_subtitle(original_file)
            return original_file


def rename_subtitle(original_file_name):
    """
    Rename subtitle
    """

    new_file_name = os.path.basename(original_file_name)
    new_file_name = new_file_name.replace(".ass", ".srt")
    new_file_name = new_file_name.replace(".ssa", ".srt")
    new_file_name = new_file_name.replace(".vtt", ".srt")
    new_file_name = new_file_name.replace(".xml", ".srt")
    new_file_name = new_file_name.replace(".json", ".srt")
    new_file_name = new_file_name.replace('.rar', '')
    new_file_name = new_file_name.replace('.zip', '')
    new_file_name = new_file_name.replace('WEBRip', 'WEB-DL')
    return new_file_name


def convert_ass_content(file_contents, type):
    """
    Convert content of vtt file to str format
    """

    replacement = re.sub(r"\{\\c\&[A-Z0-9]+\&\}", "", file_contents)

    if type == '.ssa':
        replacement = re.sub(r"&H[A-Z0-9]{6,8}", "0", replacement)

    replacement = re.sub(
        r",[cC]aption.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Caption,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r",[cC]omment.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Comment,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r",[nN]ote.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Note,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r",註釋.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Comment,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r",注釋.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Comment,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r",[cC]hat.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", r",Chat,,0000,0000,0000,,（\2）", replacement)
    replacement = re.sub(
        r"Dialogue:.+?,[lL]yrics.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", "", replacement)
    replacement = re.sub(
        r"Dialogue:.+?,.*?歌詞.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", "", replacement)
    replacement = re.sub(
        r"Dialogue:.+?,[sS]ong.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)", "", replacement)
    replacement = re.sub(
        r"Dialogue:.+?,.*?[mM]usic.*?,.*?,[0]+,[0]+,[0]+,.*?,(\{.+?\})*(.+)\n", "", replacement)
    replacement = re.sub(r"\{\\blur[0-9]+\}", r"", replacement)

    return replacement


def convert_vtt_content(file_contents):
    """
    Convert content of vtt file to str format
    """

    # 字幕顯示在上方
    # replacement = re.sub(r"(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d).*?(line:[1]*[0-9](\.[0-9]{2})*%).*?\n(.+?（)", r"\1,\2 --> \3,\4\n{\\an8}\7", file_contents)

    replacement = re.sub(
        r"(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(.+)*\n", r"\1,\2 --> \3,\4\n", file_contents)
    replacement = re.sub(
        r"(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(.+)*\n", r"\1,\2 --> \3,\4\n", replacement)
    replacement = re.sub(
        r"(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(.+)*\n", r"\1,\2 --> \3,\4\n", replacement)
    replacement = re.sub(r"WEBVTT.*?\n", "", replacement)
    replacement = re.sub(r"NOTE Netflix\n", "", replacement)
    replacement = re.sub(r"NOTE Profile:.+\n", "", replacement)
    replacement = re.sub(r"NOTE Date:.+\n", "", replacement)
    replacement = re.sub(r"NOTE Segment.+\n", "", replacement)
    replacement = re.sub(r"NOTE \/Segment.+\n", "", replacement)
    replacement = re.sub(r"Kind:[ \-\w]+\n", "", replacement)
    replacement = re.sub(r"Language:[ \-\w]+\n", "", replacement)
    replacement = re.sub(r"&lrm;", "", replacement)
    # replacement = re.sub(
    #     r"(<[^>]+>)*<[^>]+>(.*?)<\/[^>]+>(<\/[^>]+>)*", r"\2", replacement)
    replacement = re.sub(r"<\d\d:\d\d:\d\d.\d\d\d>", "", replacement)
    replacement = re.sub(r"<\\[^>]+>", "", replacement)
    replacement = re.sub(
        r"::[\-\w]+\([\-.\w\d]+\)[]*{[.,:;\(\) \-\w\d]+\n }\n", "", replacement)
    replacement = re.sub(r"Style:\n##\n", "", replacement)
    replacement = re.sub(r"(-.+?) (-.+)", r"\1\n\2", replacement)
    replacement = re.sub(r'[\t]*\n{3,}', '', replacement, re.MULTILINE)
    return replacement


def convert_xml_content(file_contents):
    """
    Convert content of xml file to str format
    """

    subs = []
    soup = BeautifulSoup(file_contents, 'xml')
    for section in soup.findAll('dia'):
        start_time = int(section.find('st').getText())
        end_time = int(section.find('et').getText())
        text = section.find('sub').getText()
        if text[0] == '[':
            text = text.replace('[', '（', 1)
        if text[-1] == ']':
            text = text[:-1] + '）'

        text = text.replace('， ', '，')

        # position = section.find('position')['vertical-margin']
        # if position and int(position.strip('%')) < 20:
        #     text = '{\\an8}' + text
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

        subs.append(pysubs2.ssaevent.SSAEvent(start_time, end_time, text))

    return subs


def convert_json_content(file_contents):
    """
    Convert content of json file to str format
    """

    subs = []
    json_data = json.loads(file_contents)
    if json_data.get('events'):
        for sub in json_data.get('events'):
            start_time = int(sub.get('tStartMs'))
            end_time = start_time + int(sub.get('dDurationMs'))
            text = sub.get('segs')[0].get('utf8')

            subs.append(pysubs2.ssaevent.SSAEvent(start_time, end_time, text))

    return convert_list_to_subtitle(subs)


def file_create(str_name_file, str_data):
    """Create a file with some data"""
    with open(str_name_file, 'w') as f:
        f.writelines(str(str_data))


def read_text_file(str_name_file):
    """Read a file text"""
    with open(str_name_file, 'r') as f:
        return f.read()


def ass_to_srt(str_name_file):
    """Convert vtt file to a srt file"""
    file_contents: str = read_text_file(str_name_file)
    str_data: str = ""
    if Path(str_name_file).suffix == '.ssa':
        str_data = str_data + convert_ass_content(file_contents, '.ssa')
    else:
        str_data = str_data + convert_ass_content(file_contents, '.ass')
    os.remove(str_name_file)
    str_name_file: str = str(Path(
        str_name_file).parent) + '/' + rename_subtitle(str_name_file)
    file_create(str_name_file, str_data)
    format_subtitle(str_name_file)
    print(os.path.basename(str_name_file) + "\t...轉檔完成")

    return str_name_file


def vtt_to_srt(str_name_file):
    """
    Convert vtt file to a srt file
    """

    file_contents: str = read_text_file(str_name_file)
    str_data: str = ""
    str_data = str_data + convert_vtt_content(file_contents)
    os.remove(str_name_file)
    str_name_file: str = str(Path(
        str_name_file).parent) + '/' + rename_subtitle(str_name_file)
    file_create(str_name_file, str_data)
    subs = pysubs2.load(str_name_file)
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

    subs.save(str_name_file)
    print(os.path.basename(str_name_file) + "\t...轉檔完成")

    return str_name_file


def srt_to_ass(str_name_file):
    """
    Convert srt file to ass file
    """

    subs = pysubs2.load(str_name_file)
    style = subs.styles["Default"].copy()
    style.fontname = 'Microsoft JhengHei UI'
    style.fontsize = 32
    style.backcolor = pysubs2.Color(0, 0, 0, 80)
    style.bold = 0
    style.outline = 0.8
    style.shadow = 0.5

    subs.styles["Default"] = style

    comment = style.copy()
    comment.fontsize = 26
    subs.styles["Comment"] = comment

    for sub in subs:
        text = sub.text
        text = text.replace('  ', ' ')
        if '**' in text:
            split_text = re.search(r"([^*]+)\\N\*\*(.+)", text)
            if split_text:
                new_sub = sub.copy()
                text = split_text.group(1)
                new_sub.text = '{\\an8}（' + split_text.group(2) + '）'
                if new_sub.text[:2] == '（（' and new_sub.text[-2:] == '））':
                    new_sub.text = new_sub.text.replace('（（', '（')
                    new_sub.text = new_sub.text.replace('））', '）')
                subs.append(new_sub)

            text = re.sub(r"^\*\*(.+)", r"（\1）", text, re.S)

        sub.text = text.strip()

    subs.sort()

    delete_list = []
    for index, sub in enumerate(subs):
        if '本節目包含置入性廣告與插播廣告' in sub.text or 'NETFLIX 原創影集' in sub.text or '字幕翻譯' in sub.text:
            delete_list.append(index)
            continue

        if sub.text[0] == '（':
            if (index > 0 and sub.start < subs[index-1].end) or (index+1 < len(subs) and sub.end > subs[index+1].start):
                sub.text = '{\\an8}' + sub.text

            sub.style = "Comment"

        if '（' not in sub.text:
            # linetv 綜藝
            # if '\\N' in sub.text:
            #     sub.text = '-' + sub.text.replace('\\N', '\\N-')
            sub.text = '{\\blur2}' + sub.text

        sub.text = sub.text.replace(' \\N', '\\N')
        sub.text = sub.text.replace('\\N ', '\\N')

        if sub.text.count('\\N') > 1:
            print(
                '行數過多：\n---------------------------------------------------------------\n' + sub.text)

    for i in reversed(delete_list):
        del subs[i]

    os.remove(str_name_file)
    str_name_file = str_name_file.replace('.srt', '.ass')
    subs.save(str_name_file)
    print(os.path.basename(str_name_file) + "\t...轉檔完成")

    return str_name_file


def xml_to_srt(str_name_file):
    """
    Convert xml file to srt file
    """

    file_contents: str = read_text_file(str_name_file)
    str_data: str = ""
    subs = convert_list_to_subtitle(convert_xml_content(file_contents))
    os.remove(str_name_file)
    str_name_file: str = str(Path(
        str_name_file).parent) + '/' + rename_subtitle(str_name_file)
    subs.save(str_name_file)
    print(os.path.basename(str_name_file) + "\t...轉檔完成\n")

    return str_name_file


def json_to_srt(str_name_file):
    """
    Convert json file to srt file
    """
    file_contents: str = read_text_file(str_name_file)
    str_data: str = ""
    subs = convert_json_content(file_contents)
    os.remove(str_name_file)
    str_name_file: str = str(Path(
        str_name_file).parent) + '/' + rename_subtitle(str_name_file)
    subs.save(str_name_file)
    print(os.path.basename(str_name_file) + "\t...轉檔完成")

    return str_name_file


def archive_subtitle(path, platform=""):
    """
    Archive subtitles
    """
    platforms = [{'id': 'nf', 'name': 'Netflix'},
                 {'id': 'kktv', 'name': 'KKTV'},
                 {'id': 'linetv', 'name': 'LineTV'},
                 {'id': 'friday', 'name': 'friDay'},
                 {'id': 'iqiyi', 'name': 'iQIYI'},
                 {'id': 'disney', 'name': 'Disney+'}]

    if platform and platform != True:
        platform = next(item for item in platforms if item['id'] == platform)[
            'name']
    else:
        platform = ''

    print("\n將字幕封裝打包：\n---------------------------------------------------------------")

    if platform:
        zipname = os.path.basename(f'{path}.WEB-DL.{platform}.zip')
    else:
        zipname = os.path.basename(f'{path}.WEB-DL.zip')

    zipname = zipname.replace(' ', '\\ ').replace(
        '(', '\\(').replace(')', '\\)')
    path = path.replace(' ', '\\ ').replace(
        '(', '\\(').replace(')', '\\)') + '/'
    print(zipname)
    command = f'cd {path} && zip -r ../{zipname} {os.path.basename(path)} . && cd ..'
    os.system(command)


def calculate_duartion(text_time):
    time_lapse = re.search(
        r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", text_time)
    if time_lapse:
        start_time = pysubs2.time.timestamp_to_ms(
            pysubs2.time.TIMESTAMP.match(time_lapse.group(1)).groups())
        end_time = pysubs2.time.timestamp_to_ms(
            pysubs2.time.TIMESTAMP.match(time_lapse.group(2)).groups())
        duration = (end_time-start_time)/1000
        print(duration)


def add_last_sub(old_file, new_file):
    old_subs = pysubs2.load(old_file)
    last_old_sub = old_subs[-1]

    new_subs = pysubs2.load(new_file)
    new_subs.sort()
    last_new_sub = new_subs[-1]
    last_two_new_sub = new_subs[-2]

    if last_two_new_sub.text == last_old_sub.text:
        print("原始行數：", len(old_subs))
        print("\n補上：" + str(last_new_sub))

        duration = last_old_sub.start - last_two_new_sub.start
        old_subs.append(pysubs2.ssaevent.SSAEvent(
            last_new_sub.start+duration, last_new_sub.end+duration, last_new_sub.text))
        old_subs.save(old_file)
        print("\n修正後行數：", len(old_subs))


def walk_dir(top_most_path, args):
    """
    Walk a directory
    """
    if args.merge and args.merge != True:
        print(
            f'\n合併所有字幕片段：\n---------------------------------------------------------------\n{args.merge}\n')
        fila_path = f'{Path(top_most_path).parent.absolute()}/{args.merge}'
        with open(fila_path, 'wb') as merge_file:
            for segment in sorted(os.listdir(top_most_path)):
                with open(os.path.join(top_most_path, segment), 'rb') as tmp:
                    shutil.copyfileobj(tmp, merge_file)
        if os.path.exists(top_most_path):
            shutil.rmtree(top_most_path)
        exit(0)

    for file in sorted(os.listdir(top_most_path)):
        pathname = os.path.join(top_most_path, file)
        filename = os.path.basename(pathname)

        if Path(filename).suffix in SUBTITLE_FORMAT:
            if args.merge:
                episode = re.search(
                    r'(.*?)([sS][0-9]{2})*([eE])*([0-9]+)(.+)', filename)

                if episode and episode.group(4):
                    length = len(episode.group(4))
                    episode_num = int(episode.group(4))

                    if episode.group(1) and episode.group(2) and episode.group(3) and episode.group(5):
                        next_file = str(Path(pathname).parent) + '/' + episode.group(1) + episode.group(
                            2) + episode.group(3) + str(episode_num+1).zfill(length) + episode.group(5)
                    else:
                        next_file = str(Path(pathname).parent) + '/' + episode.group(
                            1) + str(episode_num+1).zfill(length) + episode.group(5)

                    if episode_num % 2 != 0 and os.path.exists(next_file) and Path(next_file).suffix == '.srt':
                        print(episode_num, next_file)
                        merge_subtitle(pathname, next_file)
            else:
                handle_subtitle(args, pathname, False)

    if args.zip:
        archive_subtitle(top_most_path, args.zip)


def handle_subtitle(args, subtitle, print_log=True):

    if not os.path.exists(subtitle):
        raise argparse.ArgumentTypeError(subtitle + " 檔案不存在\n")

    convert_utf8(subtitle)

    if args.convert:
        convert_subtitle(subtitle, args.convert, True, print_log)
    elif args.shift:
        offset = float(args.shift)
        shift_subtitle(subtitle, offset, args.start)
    elif args.fps:
        frame_rate = float(args.fps)
        change_subtitle_fps(subtitle, frame_rate)
    elif args.calculate:
        calculate_duartion(args.calculate)
    elif args.add_last_sub:
        convert_utf8(args.add_last_sub)
        add_last_sub(subtitle, args.add_last_sub)
    elif args.merge:
        second_subtitle = args.merge
        convert_utf8(second_subtitle)
        if not os.path.exists(second_subtitle):
            raise argparse.ArgumentTypeError(second_subtitle + " 檔案不存在\n")

        if Path(second_subtitle).suffix == '.srt':
            merge_subtitle(subtitle, second_subtitle)
        else:
            raise argparse.ArgumentTypeError("只提供.srt檔案合併\n")

    else:
        translate_subtitle(convert_subtitle(
            subtitle, args.convert), args.translate, args.remove_cast)


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='字幕處理')
    parser.add_argument('path', help='欲修改字幕檔案的位置')
    parser.add_argument('-t',
                        '--translate',
                        dest='translate',
                        nargs='?',
                        const=True,
                        help='錯字修正')
    parser.add_argument('-r',
                        '--remove_cast',
                        dest='remove_cast',
                        nargs='?',
                        const=True,
                        help='刪除演員')
    parser.add_argument('-c',
                        '--convert',
                        dest='convert',
                        type=subtitle_format,
                        nargs='?',
                        const=True,
                        help='字幕轉成srt檔')
    parser.add_argument('-s',
                        '--shift',
                        dest='shift',
                        type=float,
                        help='平移字幕')
    parser.add_argument('-ts',
                        '--start',
                        dest='start',
                        help='起始時間')
    parser.add_argument('-f',
                        '--fps',
                        dest='fps',
                        help='調整字幕幀率')
    parser.add_argument('-m',
                        '--merge',
                        dest='merge',
                        nargs='?',
                        const=True,
                        help='合併字幕')
    parser.add_argument('-z',
                        '--zip',
                        dest='zip',
                        nargs='?',
                        const=True,
                        help='打包字幕')
    parser.add_argument('-cal',
                        '--calculate',
                        dest='calculate',
                        help='計算時間差')
    parser.add_argument('-al',
                        '--add_last_sub',
                        dest='add_last_sub',
                        help='加入最後一條字幕')

    args = parser.parse_args()

    path = args.path

    if os.path.isdir(path):
        walk_dir(path, args)
    elif os.path.isfile(path):
        if Path(path).suffix in ARCHIVE_FORMAT:

            extract_command = 'unar \'' + path + \
                '\' -o ' + str(Path(path).parent)
            result = re.search(r'Successfully extracted to "(.+?)"',
                               subprocess.getoutput(extract_command))
            if result:
                output_path = result.group(1)
                if os.path.isdir(output_path):
                    walk_dir(output_path, args)
                else:
                    handle_subtitle(args, output_path)
        elif Path(path).suffix in SUBTITLE_FORMAT:
            handle_subtitle(args, path)
        else:
            raise argparse.ArgumentTypeError(
                os.path.basename(path) + " 非字幕檔\n")
    else:
        raise argparse.ArgumentTypeError(str(path) + " 非檔案正確路徑\n")


if __name__ == "__main__":
    main()
    # print(get_encoding_type(
    #     '/Volumes/GoogleDrive/我的雲端硬碟/影片/日劇/拜託請愛我/第一季/拜託請愛我 (2016).S01E01.zh.srt'))
    # print(get_line_width('就現銀波區警察署長趙甲洙的性侵害嫌疑的第一次審判中'))
    # print(fix_overlength('明明很想留在 研究室裡 結果卻只有我留下來了'))
