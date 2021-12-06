# -*- coding: UTF-8 -*-

"""
This module is to download subtitle from KKTV、LineTV、FriDay.
"""
import re
import os
import argparse
from services import kktv, linetv, friday, iqiyi, disney
from common.utils import get_static_html, get_dynamic_html, get_ip_location


def season_episode_type(arg_value, pat=re.compile(r'[sS]\d{1,}([eE]\d{1,})*')):
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError('指定季數與集數不正確')
    return arg_value


def language_type(arg_value, pat=re.compile(r'en|zh-Hant|zh-HK|all')):
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError('目前只提供英語、台繁、港繁和全部的字幕')
    return arg_value


def print_usage():
    """Show a info message about the usage"""
    print("\n使用方式：\tpython3 download_subtitle.py url [S01][E01]\n")
    print("\t\turl\t\t- 欲下載的劇集字幕的網站")
    print("\t\tS[0-9]E[0-9]\t- 下載第[0-9]季 第[0-9]集\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='從 KKTV、LineTV、FriDay影音、愛奇藝 下載劇集、電影、綜藝、動漫等字幕')
    parser.add_argument('url',
                        help='欲下載的劇集字幕的網址')
    parser.add_argument('-e',
                        '--episode',
                        dest='episode',
                        type=season_episode_type,
                        help='下載 第[0-9]季 第[0-9]集')
    parser.add_argument('-l',
                        '--last-episode',
                        dest='last_episode',
                        action='store_true',
                        help='下載 最新一集')
    parser.add_argument('-f',
                        '--from-episode',
                        dest='from_episode',
                        type=season_episode_type,
                        help='下載 第[0-9]季 第[0-9]集 到 該季最後一集')
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
                        help='語言（英語、台繁、港繁）')
    args = parser.parse_args()

    if (args.from_episode and args.last_episode):
        parser.error("-l 與 -f 不能共用")

    if (args.episode and args.from_episode):
        parser.error("-e 與 -f 不能共用")

    query_url = args.url.strip()
    output = args.output
    if not output:
        output = str(os.getcwd()) + '/'
    else:
        output += '/'

    download_season = ''
    download_episode = ''
    if args.episode:
        download_season = re.search(
            r'[sS](\d{1,})', args.episode).group(1).zfill(2)
        if re.search(r'[eE]\d{1,}', args.episode):
            download_episode = re.search(
                r'[eE](\d{1,})', args.episode).group(1).zfill(2)

    last_episode = args.last_episode

    from_season = ''
    from_episode = ''
    if args.from_episode:
        from_season = re.search(
            r'[sS](\d{1,})', args.from_episode).group(1).zfill(2)
        if re.search(r'[eE]\d{1,}', args.from_episode):
            from_episode = re.search(
                r'[eE](\d{1,})', args.from_episode).group(1).zfill(2)

    email = args.email
    password = args.password
    language = args.language

    ip = get_ip_location()
    print(
        f"目前位置：{ip['country']}（IP: {ip['query']}）\n")

    kktv_id_search = re.search(
        r'https:\/\/www\.kktv\.me\/titles\/(.+)', query_url)
    linetv_id_search = re.search(
        r'https:\/\/www\.linetv\.tw\/drama\/(.+?)\/eps\/1', query_url)
    friday_id_search = re.search(
        r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/(.+?)', query_url)
    iqiyi_search = re.search(r'https:\/\/www\.iq\.com', query_url)
    disney_plus_search = re.search(
        r'https:\/\/www\.disneyplus\.com', query_url)

    if kktv_id_search:
        drama_id = kktv_id_search.group(1)
        if drama_id:
            query_url = f'https://www.kktv.me/play/{drama_id}010001'
            kktv.download_subtitle(get_dynamic_html(query_url),
                                   output,
                                   drama_id,
                                   download_season,
                                   download_episode,
                                   last_episode,
                                   from_season,
                                   from_episode)
    elif linetv_id_search:
        drama_id = linetv_id_search.group(1)
        linetv.download_subtitle(get_static_html(query_url),
                                 output,
                                 drama_id,
                                 download_season,
                                 download_episode,
                                 last_episode,
                                 from_season,
                                 from_episode)
    elif friday_id_search:
        drama_id = friday_id_search.group(1)
        friday.download_subtitle(get_dynamic_html(query_url),
                                 output,
                                 drama_id,
                                 download_season,
                                 download_episode,
                                 last_episode,
                                 from_season,
                                 from_episode)
    elif iqiyi_search:
        iqiyi.download_subtitle(
            get_dynamic_html(query_url), output)
    elif disney_plus_search:
        if email and password:
            disney.download_subtitle(get_dynamic_html('https://www.disneyplus.com/zh-hant/login'), query_url,
                                     email.strip(), password.strip(), output, download_season, language)
        else:
            print("Disney+需要帳號密碼登入")
            exit(1)
    else:
        print("目前只支持從\n1. KKTV\t\t下載電影、劇集、綜藝、動漫字幕\n2. LineTV\t下載劇集、綜藝字幕\n3. FriDay影音\t下載劇集、電影、綜藝、動漫字幕\n4. 愛奇藝\t下載劇集\n4. Disney+\t下載劇集\n\n請確認網站網址無誤")
