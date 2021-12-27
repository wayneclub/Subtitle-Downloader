# -*- coding: UTF-8 -*-

"""
This module is to download subtitle from KKTV、LineTV、FriDay.
"""
import re
import os
import argparse
import logging
from services import kktv, linetv, friday, iqiyi, disney
from services.hbogo import HBOGO
from common.utils import get_static_html, get_dynamic_html, get_ip_location


def language_type(arg_value, pat=re.compile(r'en|zh-Hant|zh-HK|zh-Hans|all')):
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError('目前只提供英語、台繁、港繁、簡體和全部的字幕')
    return arg_value


def print_usage():
    """Show a info message about the usage"""
    print("\n使用方式：\tpython download_subtitle.py url\n")
    print("\t\turl\t\t- 欲下載的劇集字幕的網站")
    print("\t\t-S [0-9]\t- 下載第[0-9]季\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='從Disney Plus、HBOGO Asia、KKTV、LineTV、friDay影音、愛奇藝 下載劇集、電影、綜藝、動漫等字幕')
    parser.add_argument('url',
                        help='欲下載的劇集字幕的網址')
    parser.add_argument('-s',
                        '--season',
                        dest='season',
                        type=int,
                        help='下載 第[0-9]季')
    parser.add_argument('-l',
                        '--last-episode',
                        dest='last_episode',
                        action='store_true',
                        help='下載 最新一集')
    parser.add_argument('-o',
                        '--output',
                        dest='output',
                        help='下載路徑')
    parser.add_argument('-email',
                        '--email',
                        dest='email',
                        help='串流平台帳號')
    parser.add_argument('-password',
                        '--password',
                        dest='password',
                        help='串流平台密碼')
    parser.add_argument('-lang',
                        '--language',
                        dest='language',
                        type=language_type,
                        help='語言（英語、台繁、港繁、簡中）')
    parser.add_argument('-a',
                        '--audio',
                        dest='audio',
                        nargs='?',
                        const=True,
                        help='下載（台配、港配）音軌')
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='enable debug logging',
    )
    args = parser.parse_args()

    if (args.season and args.last_episode):
        parser.error("-l 與 -s 不能共用")

    if args.debug:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO,
        )

    query_url = args.url.strip()
    output = args.output
    if not output:
        output = os.getcwd()

    download_season = ''
    if args.season:
        download_season = int(args.season)

    last_episode = args.last_episode

    email = args.email
    password = args.password
    language = args.language
    download_audio = args.audio

    ip = get_ip_location()
    logging.info(
        '目前位置：%s（ip: %s）\n', ip['country'], ip['query'])

    kktv_id_search = re.search(
        r'https:\/\/www\.kktv\.me\/titles\/(.+)', query_url)
    linetv_id_search = re.search(
        r'https:\/\/www\.linetv\.tw\/drama\/(.+?)\/eps\/1', query_url)
    friday_genre_search = re.search(
        r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/.+', query_url)
    iqiyi_search = re.search(r'https:\/\/www\.iq\.com', query_url)
    disney_genre_search = re.search(
        r'https:\/\/www\.disneyplus\.com\/.*(series|movies)\/.+', query_url)
    hbogo_search = re.search(
        r'https:\/\/www\.hbogoasia\..+', query_url)

    if kktv_id_search:
        drama_id = kktv_id_search.group(1)
        if drama_id:
            query_url = f'https://www.kktv.me/play/{drama_id}010001'
            kktv.download_subtitle(get_dynamic_html(query_url),
                                   output,
                                   drama_id,
                                   download_season,
                                   last_episode)
    elif linetv_id_search:
        drama_id = linetv_id_search.group(1)
        linetv.download_subtitle(get_static_html(query_url),
                                 output,
                                 drama_id,
                                 last_episode)
    elif friday_genre_search:
        genre = friday_genre_search.group(1)
        friday.download_subtitle(get_dynamic_html(query_url),
                                 output,
                                 genre,
                                 download_season,
                                 last_episode)
    elif iqiyi_search:
        iqiyi.download_subtitle(
            get_dynamic_html(query_url), output)
    elif disney_genre_search:
        genre = disney_genre_search.group(1)
        if email and password:
            disney.download_subtitle(disney.login(
                email.strip(), password.strip()), query_url, genre, output, download_season, language, download_audio)
        else:
            print("Disney+需要帳號密碼登入")
            exit(1)
    elif hbogo_search:
        hbogo = HBOGO(args)
        hbogo.main()
    else:
        print("目前只支持從\n1. KKTV\t\t下載電影、劇集、綜藝、動漫字幕\n2. LineTV\t下載劇集、綜藝字幕\n3. FriDay影音\t下載劇集、電影、綜藝、動漫字幕\n4. 愛奇藝\t下載劇集\n4. Disney+\t下載劇集\n\n請確認網站網址無誤")
