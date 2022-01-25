#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from stream services.
"""

import argparse
import logging
from datetime import datetime
from common.utils import get_locale, get_ip_location
from services.disneyplus import DisneyPlus
from services.hbogoasia import HBOGOAsia
from services.iqiyi import IQIYI
from services.friday import Friday
from services.linetv import LineTV
from services.kktv import KKTV
from services.viu import Viu
from services.netflix import Netflix
from services.itunes import iTunes
from services.catchplay import CatchPlay
from services.wetv import WeTV


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
                        type=int,
                        help=_("download season [0-9]"))
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

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG,
            handlers=[
                logging.FileHandler(
                    f"Subtitle-Downloader_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO,
        )

    ip = get_ip_location()
    logging.info(
        'ip: %s (%s)', ip['ip'], ip['country'])

    if 'kktv' in args.url:
        kktv = KKTV(args)
        kktv.main()
    elif 'linetv' in args.url:
        linetv = LineTV(args)
        linetv.main()
    elif 'video.friday' in args.url:
        friday = Friday(args)
        friday.main()
    elif 'iq.com' in args.url:
        iqiyi = IQIYI(args)
        iqiyi.main()
    elif 'disneyplus' in args.url:
        disney_plus = DisneyPlus(args)
        disney_plus.main()
    elif 'hbogoasia' in args.url:
        hbogoasia = HBOGOAsia(args)
        hbogoasia.main()
    elif 'viu.com' in args.url:
        viu = Viu(args)
        viu.main()
    elif 'netflix.com' in args.url:
        netflix = Netflix(args)
        netflix.main()
    elif 'itunes.apple.com' in args.url:
        itunes = iTunes(args)
        itunes.main()
    elif 'catchplay.com' in args.url:
        catchplay = CatchPlay(args)
        catchplay.main()
    elif 'wetv.vip' in args.url:
        wetv = WeTV(args)
        wetv.main()
    else:
        logging.info(
            _("Only support downloading subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iq.com, Viu, CatchPlay, WeTV ,and iTunes."))
