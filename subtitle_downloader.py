#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from stream services.
"""

import argparse
import logging
from datetime import datetime
import os
from configs.config import Config, script_name, __version__
from services.kktv import KKTV
from services.linetv import LineTV
from services.friday import Friday
from services.catchplay import CatchPlay
from services.iqiyi import IQIYI
from services.nowplayer import NowPlayer
from services.wetv import WeTV
from services.viu import Viu
from services.nowe import NowE
from services.disneyplus.disneyplus import DisneyPlus
from services.hbogoasia import HBOGOAsia
from services.itunes import iTunes
from utils.helper import get_locale
from utils.proxy_environ import proxy_env

if __name__ == "__main__":
    _ = get_locale('main')

    parser = argparse.ArgumentParser(
        description=_(
            "Download subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iq.com, and Viu"),
        add_help=False)
    parser.add_argument('url',
                        help=_("series's/movie's link"))
    parser.add_argument('-s',
                        '--season',
                        dest='season',
                        help=_("download season [0-9]"))
    parser.add_argument('-e',
                        '--episode',
                        dest='episode',
                        help=_("download episode [0-9]"))
    parser.add_argument('-l',
                        '--last-episode',
                        dest='last_episode',
                        action='store_true',
                        help=_("download the latest episode"))
    parser.add_argument('-o',
                        '--output',
                        dest='output',
                        help=_("output directory"))
    parser.add_argument('-email',
                        '--email',
                        dest='email',
                        help=_("account for Disney Plus and HBOGO Asia"))
    parser.add_argument('-password',
                        '--password',
                        dest='password',
                        help=_("password for Disney Plus and HBOGO Asia"))
    parser.add_argument('-slang',
                        '--subtitle-language',
                        dest='subtitle_language',
                        help=_("languages of subtitles; use commas to separate multiple languages"))
    parser.add_argument('-alang',
                        '--audio-language',
                        dest='audio_language',
                        help=_("languages of audio-tracks; use commas to separate multiple languages"))
    parser.add_argument(
        '-region',
        '--region',
        dest='region',
        help=_("streaming service's region"),
    )
    parser.add_argument(
        '-locale',
        '--locale',
        dest='locale',
        help=_("interface language"),
    )
    parser.add_argument('-p',
                        '--proxy',
                        dest='proxy',
                        nargs='?',
                        const=True,
                        help="proxy")
    parser.add_argument("--pv",
                        '--private-vpn',
                        action="store",
                        dest="privtvpn",
                        help="add country for privtvpn proxies.",
                        default=0)
    parser.add_argument("-n",
                        '--nord-vpn',
                        action="store",
                        dest="nordvpn",
                        help="add country for nordvpn proxies.",
                        default=0)
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help=_("enable debug logging"),
    )
    parser.add_argument(
        '-h',
        '--help',
        action='help',
        default=argparse.SUPPRESS,
        help=_("show this help message and exit")
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='{script_name} {version}'.format(
            script_name=script_name, version=__version__)
    )

    args = parser.parse_args()

    config = Config()
    paths = config.paths()

    if args.debug:
        os.makedirs(paths['logs'], exist_ok=True)
        log_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file_path = os.path.join(
            paths['logs'], f"Subtitle-Downloader_{log_time}.log")
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG,
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO,
        )

    ip_info = proxy_env(args).Load()
    args.proxy = ip_info

    start = datetime.now()
    if 'kktv' in args.url:
        kktv = KKTV(args)
        kktv.main()
    elif 'linetv' in args.url:
        linetv = LineTV(args)
        linetv.main()
    elif 'video.friday' in args.url:
        friday = Friday(args)
        friday.main()
    elif 'catchplay.com' in args.url:
        catchplay = CatchPlay(args)
        catchplay.main()
    elif 'iq.com' in args.url:
        iqiyi = IQIYI(args)
        iqiyi.main()
    elif 'wetv.vip' in args.url:
        wetv = WeTV(args)
        wetv.main()
    elif 'viu.com' in args.url:
        viu = Viu(args)
        viu.main()
    elif 'nowe.com' in args.url:
        nowe = NowE(args)
        nowe.main()
    elif 'nowplayer' in args.url:
        nowplayer = NowPlayer(args)
        nowplayer.main()
    elif 'disneyplus' in args.url:
        disney_plus = DisneyPlus(args)
        disney_plus.main()
    elif 'hbogoasia' in args.url:
        hbogoasia = HBOGOAsia(args)
        hbogoasia.main()
    elif 'itunes.apple.com' in args.url:
        itunes = iTunes(args)
        itunes.main()
    else:
        logging.info(
            _("Only support downloading subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iq.com, Viu, CatchPlay, WeTV ,and iTunes."))

    logging.info("\n%s took %s seconds", script_name,
                 int(float((datetime.now() - start).total_seconds())))
