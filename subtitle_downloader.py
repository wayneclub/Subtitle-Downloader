#!/usr/bin/python3
# coding: utf-8

"""
This module is to download subtitle from stream services.
"""
import argparse
import logging
from datetime import datetime
import os
import sys
import validators
from configs.config import Platform, config, app_name, __version__, filenames
from services import service_map
from utils.helper import get_locale
from utils.io import load_toml


def main() -> None:
    _ = get_locale('main')

    parser = argparse.ArgumentParser(
        description=_(
            "Support downloading subtitles from multiple streaming services, such as Disney+, HBOGO Asia, KKTV, LineTV, friDay Video, MyVideo, CatchPlay, iq.com, Viu (support HK and SG without vpn), WeTV, NowE, Now Player, AppleTV+, iTunes and etc."),
        add_help=False)
    parser.add_argument('url',
                        help=_("series's/movie's url"))
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
    parser.add_argument('-slang',
                        '--subtitle-language',
                        dest='subtitle_language',
                        help=_("languages of subtitles; use commas to separate multiple languages"))
    parser.add_argument('-alang',
                        '--audio-language',
                        dest='audio_language',
                        help=_("languages of audio-tracks; use commas to separate multiple languages"))
    parser.add_argument('-sf',
                        '--subtitle-format',
                        dest='subtitle_format',
                        help=_("subtitles format: .srt or .ass"))
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
                        help=_("proxy"))
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
        version=f'{app_name} {__version__}',
        help=_("app's version")
    )

    args = parser.parse_args()

    if args.debug:
        os.makedirs(config.directories['logs'], exist_ok=True)
        log_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file_path = str(filenames.log).format(
            app_name=app_name, log_time=log_time)
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

    start = datetime.now()

    if not validators.url(args.url):
        logging.warning(
            _("\nPlease input correct url!"))
        sys.exit(0)

    service = next((service for service in service_map
                   if service['keyword'] in args.url), None)

    if service:
        log = logging.getLogger(service['class'].__module__)

        service_config = load_toml(
            str(filenames.config).format(service=service['name']))

        args.log = log
        args.config = service_config
        args.platform = service['name']
        service['class'](args).main()
    else:
        logging.warning(
            _("\nOnly support downloading subtitles from %s"), ', '.join(sorted([v for k, v in Platform.__dict__.items()
                                                                                 if not k.startswith("__")])))
        sys.exit(1)

    logging.info("\n%s took %s seconds", app_name,
                 int(float((datetime.now() - start).total_seconds())))


if __name__ == "__main__":
    main()
