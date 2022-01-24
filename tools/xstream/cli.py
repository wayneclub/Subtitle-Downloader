import sys
import base64
import platform
from pathlib import Path
from logging import Logger
from argparse import ArgumentParser

from tools.xstream.cmdargs import CmdArgs
from tools.xstream.daemon import Daemon
from tools.xstream.version import __version__
from tools.xstream.headers.default import Headers
from tools.xstream.log import setup_logger


def command_handler(logger: Logger, args: CmdArgs):
    '''
    对命令参数进行校验和修正
    '''
    if args.live_duration == '':
        args.live_duration = 0.0
    else:
        hms = args.live_duration.split(':')
        assert len(
            hms) == 3, '--live-duration format is HH:MM:SS, example: 00:00:30'
        assert len(
            hms[1]) <= 2, '--live-duration minute length must less than or equal to 2'
        assert len(
            hms[2]) <= 2, '--live-duration second length must less than or equal to 2'
        if hms[0].isdigit() and hms[1].isdigit() and hms[2].isdigit():
            assert float(
                hms[1]) <= 60.0, '--live-duration minute must less than or equal to 60'
            assert float(
                hms[2]) <= 60.0, '--live-duration second must less than or equal to 60'
            args.live_duration = float(
                hms[0]) * 60 * 60 + float(hms[1]) * 60 + float(hms[2])
    try:
        args.live_utc_offset = int(args.live_utc_offset)
        args.live_refresh_interval = int(args.live_refresh_interval)
    except Exception:
        assert False, '--live-utc-offset can not be convert to int value'
    logger.debug(f'set --live-duration to {args.live_duration}')
    if args.video_only is True and args.audio_only is True:
        assert False, '--video-only and --audio-only cannot be used at the same time'
    args.save_dir = Path(args.save_dir)
    if args.save_dir.exists() is False:
        args.save_dir.mkdir()
    logger.debug(f'set --save-dir to {args.save_dir.resolve().as_posix()}')
    args.headers = Headers(logger).get(args)
    args.limit_per_host = int(args.limit_per_host)
    logger.debug(f'set --limit-per-host to {args.limit_per_host}')
    if args.key is not None:
        infos = args.key.split(':')
        assert len(infos) == 2, 'DASH Stream decryption key format error !'
        # assert len(infos[0]) == 32, 'DASH Stream decryption key @KID must be 32 length hex string !'
        assert len(
            infos[1]) == 32, 'DASH Stream decryption key @k must be 32 length hex string !'
    logger.debug(f'set --key to {args.key}')
    if args.b64key is not None:
        try:
            _ = base64.b64decode(args.b64key)
        except Exception as e:
            raise e
    if args.hexiv is not None:
        if args.hexiv.lower().startswith('0x'):
            args.hexiv = args.hexiv.lower()[2:]
    logger.debug(f'set --b64key to {args.b64key}')
    logger.debug(f'set --hexiv to {args.hexiv}')

    if getattr(sys, 'frozen', False):
        bin_path = Path(sys.executable).parent / 'binaries'
    else:
        bin_path = Path(__file__).parent.parent / 'binaries'
    if bin_path.exists() is False:
        args.ffmpeg = 'ffmpeg'
        args.mp4decrypt = 'mp4decrypt'
        args.mp4box = 'mp4box'
        logger.warning(f'binaries folder is not exist > {bin_path}')
    else:
        if platform.system() == 'Windows':
            args.ffmpeg = (bin_path / 'ffmpeg.exe').resolve().as_posix()
            args.mp4decrypt = (
                bin_path / 'mp4decrypt.exe').resolve().as_posix()
            args.mp4box = (bin_path / 'mp4box.exe').resolve().as_posix()
        else:
            args.ffmpeg = (bin_path / 'ffmpeg').resolve().as_posix()
            args.mp4decrypt = (bin_path / 'mp4decrypt').resolve().as_posix()
            args.mp4box = (bin_path / 'mp4box').resolve().as_posix()
    logger.debug(f'ffmpeg {args.ffmpeg}')
    logger.debug(f'mp4decrypt {args.mp4decrypt}')
    logger.debug(f'mp4box {args.mp4box}')
    try:
        args.redl_code = [int(_.strip())
                          for _ in args.redl_code.split(',') if _ != '']
    except Exception as e:
        logger.error(f'parse --redl-code option failed', exc_info=e)
        args.redl_code = []


def main():
    def print_version():
        print(
            f'version {__version__}, A downloader that download the HLS/DASH stream.')

    parser = ArgumentParser(prog='XstreamDL-CLI', usage='XstreamDL-CLI [OPTION]... URL/FILE/FOLDER...',
                            description='A downloader that download the HLS/DASH stream', add_help=False)
    parser.add_argument('-v', '--version', action='store_true',
                        help='print version and exit')
    parser.add_argument('-h', '--help', action='store_true',
                        help='print help message and exit')
    parser.add_argument('--live', action='store_true', help='live mode')
    parser.add_argument('--live-duration', default='',
                        help='live record time, format HH:MM:SS, example 00:00:30 will record about 30s')
    parser.add_argument('--live-utc-offset', default='0',
                        help='the value is used to correct utc time')
    parser.add_argument('--live-refresh-interval',
                        default='3', help='live refresh interval')
    parser.add_argument('--name', default='', help='specific stream base name')
    parser.add_argument('--base-url', default='',
                        help='set base url for Stream')
    parser.add_argument('--resolution', default='', choices=[
                        '', '270', '360', '480', '540', '576', '720', '1080', '2160'], help='auto choose target quality')
    parser.add_argument('--best-quality', action='store_true',
                        help='auto choose best quality for dash streams')
    parser.add_argument('--video-only', action='store_true',
                        help='only choose video stream when use --best-quality')
    parser.add_argument('--audio-only', action='store_true',
                        help='only choose audio stream when use --best-quality')
    parser.add_argument('--all-videos', action='store_true',
                        help='choose all video stream to download')
    parser.add_argument('--all-audios', action='store_true',
                        help='choose all audio stream to download')
    parser.add_argument('--service', default='',
                        help='set serviceLocation for BaseURL choose')
    parser.add_argument('--save-dir', default='Downloads',
                        help='set save dir for Stream')
    parser.add_argument('--select', action='store_true',
                        help='show stream to select and download, default is to download all')
    parser.add_argument('--multi-s', action='store_true',
                        help='use this option when S tag number > 0')
    parser.add_argument('--disable-force-close', action='store_true',
                        help='default make all connections closed securely, but it will make DL speed slower')
    parser.add_argument('--limit-per-host', default=4,
                        help='increase the value if your connection to the stream host is poor, suggest >100 for DASH stream')
    parser.add_argument('--headers', default='headers.json',
                        help='read headers from headers.json, you can also use custom config')
    parser.add_argument('--url-patch', default='',
                        help='add some custom strings for all segments link')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite output files')
    parser.add_argument('--raw-concat', action='store_true',
                        help='concat content as raw')
    parser.add_argument('--disable-auto-concat',
                        action='store_true', help='disable auto-concat')
    parser.add_argument('--enable-auto-delete', action='store_true',
                        help='enable auto-delete files after concat success')
    parser.add_argument('--disable-auto-decrypt', action='store_true',
                        help='disable auto-decrypt segments before dump to disk')
    parser.add_argument('--key', default=None,
                        help='<id>:<k>, <id> is either a track ID in decimal or a 128-bit KID in hex, <k> is a 128-bit key in hex')
    parser.add_argument('--b64key', default=None,
                        help='base64 format aes key, only for HLS standard AES-128-CBC encryption')
    parser.add_argument('--hexiv', default=None, help='hex format aes iv')
    parser.add_argument('--proxy', default='',
                        help='use socks/http proxy, e.g. socks5://127.0.0.1:10808 or http://127.0.0.1:10809')
    parser.add_argument('--disable-auto-exit', action='store_true',
                        help='disable auto exit after download end, GUI will use this option')
    parser.add_argument('--parse-only', action='store_true',
                        help='parse only, not to download')
    parser.add_argument('--show-init', action='store_true',
                        help='show initialization to help you identify same name stream')
    parser.add_argument('--index-to-name', action='store_true',
                        help='some dash live have the same name for different stream, use this option to avoid')
    parser.add_argument('--log-level', default='INFO', choices=[
                        'DEBUG', 'INFO', 'WARNING', 'ERROR'], help='set log level, default is INFO')
    parser.add_argument('--redl-code', default='',
                        help='re-download set of response status codes , e.g. 408,500,502,503,504')
    parser.add_argument('--hide-load-metadata', action='store_true',
                        help='hide `Load #EXT-X-MEDIA metadata` balabala')
    parser.add_argument('URI', nargs='*', help='URL/FILE/FOLDER string')
    args = parser.parse_args()
    if args.help:
        print_version()
        parser.print_help()
        sys.exit()
    if args.version:
        print_version()
        sys.exit()
    if len(args.URI) == 0:
        try:
            uri = input(
                'Paste your URL/FILE/FOLDER string at the end of commands, plz.\nCtrl C to exit or input here:')
        except KeyboardInterrupt:
            sys.exit()
        if uri.strip() != '':
            args.URI.append(uri.strip())
    if len(args.URI) == 0:
        sys.exit('No URL/FILE/FOLDER input')
    logger = setup_logger('XstreamDL', args.log_level)
    command_handler(logger, args)
    logger.info(f'use {__version__}, set URI to {args.URI}')
    logger.debug(f'args => {args}')
    daemon = Daemon(logger, args)
    daemon.daemon()
    if args.disable_auto_exit:
        _ = input('press any key to exit.')


if __name__ == '__main__':
    main()
