# -*- coding: UTF-8 -*-

"""
This module is to download subtitle from KKTV、LineTV、FriDay.
"""

import re
import argparse
import logging
from common.utils import get_locale, get_ip_location
from services.disneyplus import DisneyPlus
from services.hbogoasia import HBOGOAsia
from services.iqiyi import IQIYI
from services.friday import Friday
from services.linetv import LineTV
from services.kktv import KKTV


if __name__ == "__main__":
    _ = get_locale('main')

    parser = argparse.ArgumentParser(
        description=_("Download subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iq.com."))
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
                        help=_('download the latest episode'))
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
                        help=_("languages of HBOGO Asia's and Disney Plus's subtitles to download (optional) separated by commas"))
    parser.add_argument('-alang',
                        '--audio-language',
                        dest='audio_language',
                        help=_("languages of Disney Plus's audio-tracks to download (optional) separated by commas"))
    parser.add_argument(
        '-locale',
        '--locale',
        dest='locale',
        help='locale for logging messages',
    )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='enable debug logging',
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO,
        )

    ip = get_ip_location()
    logging.info(
        'ip: %s (%s)', ip['ip'], ip['country'])

    kktv_search = re.search(
        r'https:\/\/www\.kktv\.me\/titles\/.+', args.url)
    linetv_search = re.search(
        r'https:\/\/www\.linetv\.tw\/drama\/.+?\/eps\/1', args.url)
    friday_search = re.search(
        r'https:\/\/video\.friday\.tw\/(drama|anime|movie|show)\/detail\/.+', args.url)
    iqiyi_search = re.search(r'https:\/\/www\.iq\.com', args.url)
    disney_search = re.search(
        r'https:\/\/www\.disneyplus\.com\/.*(series|movies)\/.+', args.url)
    hbogoasia_search = re.search(
        r'https:\/\/www\.hbogoasia\..+', args.url)

    if kktv_search:
        kktv = KKTV(args)
        kktv.main()
    elif linetv_search:
        linetv = LineTV(args)
        linetv.main()
    elif friday_search:
        friday = Friday(args)
        friday.main()
    elif iqiyi_search:
        iqiyi = IQIYI(args)
        iqiyi.main()
    elif disney_search:
        disney_plus = DisneyPlus(args)
        disney_plus.main()
    elif hbogoasia_search:
        hbogoasia = HBOGOAsia(args)
        hbogoasia.main()
    else:
        logging.info(
            _("Only support downloading subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, and iq.com."))
