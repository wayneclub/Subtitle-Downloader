from typing import List
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

from tools.pyshaka.util.TextParser import TimeContext
from tools.pyshaka.text.Mp4VttParser import Mp4VttParser
from tools.pyshaka.text.Mp4TtmlParser import Mp4TtmlParser
from tools.pyshaka.text.Cue import Cue
from tools.pyshaka.log import log


class CmdArgs:
    def __init__(self):
        self.debug = None  # type: bool
        self.type = None  # type: str
        self.timescale = None  # type: int
        self.init_path = None  # type: str
        self.segments_path = None  # type: str
        self.segment_time = None  # type: float


def command_handler(args: CmdArgs):
    '''
    对命令参数进行校验和修正
    '''
    assert args.type in ['wvtt', 'ttml'], f'not support {args.type} now'
    args.timescale = int(args.timescale)
    if args.init_path:
        args.init_path = args.init_path.strip()
    args.segments_path = args.segments_path.strip()
    args.segment_time = float(args.segment_time)


def loop_nestedCues(lines: List[str], nestedCues: List[Cue], index: int, segment_time: float):
    payload = ''
    for cue in nestedCues:
        if len(cue.nestedCues) > 0:
            loop_nestedCues(lines, cue.nestedCues, index, segment_time)
        if cue.payload != '':
            if payload == '':
                payload = cue.payload
            else:
                payload = f'{payload} {cue.payload}'
        # 这里突然想不起注释掉的原因了 好像是会重复...
        # lines.append(cue)
    cue = nestedCues[0]
    payload = payload
    if payload != '':
        cue.payload = payload
        cue.startTime += segment_time * index
        cue.endTime += segment_time * index
        lines.append(cue)


def compare(cue: Cue):
    return cue.startTime


# def compare(cue1: Cue, cue2: Cue):
#     if cue1.startTime < cue2.startTime:
#         return -1
#     if cue1.startTime > cue2.startTime:
#         return 1
#     return 0


def gentm(tm: float):
    return datetime.utcfromtimestamp(tm).strftime('%H:%M:%S.%f')[:-3]


def test_parse_mp4vtt():
    mp4vttparser = Mp4VttParser()
    vttInitSegment = Path("test/assets/vtt-init.mp4").read_bytes()
    mp4vttparser.parseInit(vttInitSegment)
    vttSegment = Path("test/assets/vtt-segment.mp4").read_bytes()
    timecontext = TimeContext(
        **{'periodStart': 0, 'segmentStart': 0, 'segmentEnd': 0})
    mp4vttparser.parseMedia(vttSegment, timecontext)


def parse(args: CmdArgs):
    if args.type == 'wvtt':
        parser = Mp4VttParser()
    elif args.type == 'ttml':
        parser = Mp4TtmlParser()
    else:
        assert 1 == 0, 'never should be here'
    if args.init_path:
        init_path = Path(args.init_path)
        parser.parseInit(init_path.read_bytes())
    else:
        parser.set_timescale(args.timescale)
    segments_path = Path(args.segments_path)
    time = TimeContext(
        **{'periodStart': 0, 'segmentStart': 0, 'segmentEnd': 0})
    index = 0
    cues = []
    for segment_path in segments_path.iterdir():
        if segment_path.is_dir():
            if args.debug:
                log.debug(f'{segment_path} is not a file, skip it')
            continue
        if segment_path.suffix not in ['.mp4', '.m4s', '.dash', '.ts']:
            if args.debug:
                log.debug(
                    f"{segment_path} suffix is not in ['.mp4', '.m4s', '.dash', '.ts'], skip it")
            continue
        if args.init_path and segment_path.name == init_path.name:
            if args.debug:
                log.debug(f"{segment_path} is init_path , skip it")
            continue
        if args.debug:
            log.debug(f'start parseMedia for {segment_path}')
        _cues = parser.parseMedia(segment_path.read_bytes(), time)

        for cue in _cues:
            cue.file = segment_path.name
            if len(cue.nestedCues) > 0:
                loop_nestedCues(cues, cue.nestedCues, index, args.segment_time)
            if cue.payload != '':
                cue.startTime += args.segment_time * index
                cue.endTime += args.segment_time * index
                cues.append(cue)
        index += 1
    # 按Cue.startTime从小到大排序
    cues.sort(key=compare)
    if args.debug:
        log.debug(f'cues count {len(cues)}')
    assert len(cues) > 0, 'ohh, it is a bug...'
    # 去重
    # 1. 如果当前行的endTime等于下一行的startTime 并且下一行内容与当前行相同 取下一行的endTime作为当前行的endTime 然后去除下一行
    # 2. 否则将下一行作为当前行 再次进行比较 直到比较结束
    offset = 0
    cues_fix = []  # type: List[Cue]
    cue = cues[offset]
    while offset < len(cues) - 1:
        offset += 1
        # 跳过空的行
        next_cue = cues[offset]
        if cue.payload == '':
            cue = next_cue
            continue
        if cue.payload == next_cue.payload and cue.endTime == next_cue.startTime:
            cue.endTime = next_cue.endTime
        else:
            cues_fix.append(cue)
            cue = next_cue
    # 最后一行也不能掉
    next_cue = cues[offset]
    if cue.payload == next_cue.payload and cue.endTime == next_cue.startTime:
        cue.endTime = next_cue.endTime
    else:
        cues_fix.append(cue)
        cue = next_cue
    if args.debug:
        log.debug(
            f'after reduce duplicated lines, now lines count is {len(cues_fix)}')
    # 先用列表放内容 最后join
    contents = ["WEBVTT"]  # type: List[str]
    for cue in cues_fix:
        settings = cue._settings
        if settings:
            settings = ' ' + settings
            text = f'{gentm(cue.startTime)} --> {gentm(cue.endTime)}{settings}\n{cue.payload}'
        else:
            text = f'{gentm(cue.startTime)} --> {gentm(cue.endTime)}\n{cue.payload}'
        contents.append(text)
    content = '\n\n'.join(contents)
    segments_path.with_suffix(".vtt").write_text(content, encoding='utf-8')
    log.info(f'{len(cues_fix)} lines of subtitle was founded.')
    log.info(f'write to {segments_path.with_suffix(".vtt").resolve()}')


def main():

    parser = ArgumentParser(
        prog='dash-subtitle-extractor',
        usage='python -m pyshaka.main [OPTION]...',
        description='A tool that to parse subtitle embedded in DASH stream',
        add_help=True,
    )
    parser.add_argument('-debug', '--debug',
                        action='store_true', help='debug is needed')
    parser.add_argument(
        '-type', '--type', choices=['wvtt', 'ttml'], help='subtitle codec, only support wvtt and ttml now')
    parser.add_argument('-timescale', '--timescale', default='1000',
                        help='set timescale manually if no init segment')
    parser.add_argument('-init-path', '--init-path', help='init segment path')
    parser.add_argument('-segments-path', '--segments-path',
                        help='segments folder path')
    parser.add_argument('-segment-time', '--segment-time', default='0',
                        help='single segment duration, usually needed for ttml content, calculation method: d / timescale')
    args = parser.parse_args()  # type: CmdArgs
    command_handler(args)
    parse(args)
    # python -m pyshaka.main --init-path "test/dashvtt_subtitle_WVTT_zh-TW/init.mp4" --segments-path "test/dashvtt_subtitle_WVTT_zh-TW"


if __name__ == '__main__':
    main()
