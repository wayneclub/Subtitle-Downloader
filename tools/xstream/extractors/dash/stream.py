import re
from pathlib import Path
from typing import List, Union
from tools.xstream.models.base import BaseUri
from tools.xstream.models.stream import Stream
from tools.xstream.util.maps.codecs import AUDIO_CODECS
from tools.xstream.extractors.dash.segment import DASHSegment


class DASHStream(Stream):
    def __init__(self, index: int, uri_item: BaseUri, save_dir: Path):
        super(DASHStream, self).__init__(index, uri_item, save_dir)
        self.model = 'dash'
        self.segments = []  # type: List[DASHSegment]
        self.suffix = '.mp4'
        self.has_init_segment = False
        self.skey = ''  # type: str
        self.append_segment()

    def get_name(self):
        if self.stream_type != '':
            base_name = f'{self.name}_{self.stream_type}'
        else:
            base_name = self.name
        if 'ixigua.com' in self.home_url:
            base_name += f'_{self.index}'
        if self.codecs is not None and self.codecs != '':
            base_name += f'_{self.codecs}'
        if self.stream_type == 'subtitle' and self.lang != '':
            base_name += f'_{self.lang}'
        elif self.stream_type == 'text' and self.lang != '':
            base_name += f'_{self.lang}'
        elif self.stream_type == 'video' and self.resolution != '':
            base_name += f'_{self.resolution}'
        elif self.stream_type == 'audio' and self.lang != '':
            base_name += f'_{self.lang}'
        if self.stream_type in ['audio', 'video'] and self.bandwidth is not None:
            base_name += f'_{self.bandwidth / 1000:.2f}kbps'
        if self.stream_type == '' and self.skey:
            base_name += self.skey
        return base_name

    def append_segment(self):
        index = len(self.segments)
        if self.has_init_segment:
            index -= 1
        segment = DASHSegment().set_index(index).set_folder(self.save_dir)
        self.segments.append(segment)

    def update(self, stream: 'DASHStream'):
        '''
        Representation id相同可以合并
        这个时候应该重新计算时长和码率
        '''
        total_duration = self.duration + stream.duration
        if total_duration > 0:
            self.bandwidth = (stream.duration * stream.bandwidth + self.duration *
                              self.bandwidth) / (self.duration + stream.duration)
        self.duration += stream.duration
        has_init = False
        for segment in stream.segments:
            # 被合并的流的init分段 避免索引计算错误
            if segment.segment_type == 'init':
                has_init = True
                stream.segments.remove(segment)
                break
        self.segments_extend(stream.segments, has_init=has_init)

    def set_subtitle_url(self, url: str):
        self.has_init_segment = True
        self.segments[-1].set_subtitle_url(self.fix_url(url))
        # self.append_segment()

    def set_init_url(self, url: str):
        self.has_init_segment = True
        self.segments[-1].set_init_url(self.fix_url(url))
        self.append_segment()

    def set_media_url(self, url: str):
        self.segments[-1].set_media_url(self.fix_url(url))
        self.append_segment()

    def base2url(self, duration: float):
        if duration is not None:
            self.duration = duration
        self.segments[-1].set_media_url(self.base_url)
        self.append_segment()

    def set_segment_duration(self, duration: float):
        self.segments[-1].set_duration(duration)

    def set_segment_fmt_time(self, fmt_time: int):
        self.segments[-1].set_fmt_time(fmt_time)

    def set_segments_duration(self, duration: float):
        '''' init分段没有时长 这里只用设置普通分段的 '''
        for segment in self.segments:
            if segment.segment_type == 'init':
                continue
            segment.set_duration(duration)

    def get_skey(self):
        return self.skey

    def set_skey(self, aid: str, rid: str):
        _patch = ''
        if aid is not None:
            self.skey += f'{aid}'
            _patch = '_'
        if rid is not None:
            self.skey += f'{_patch}{rid}'.replace('/', '_')

    def set_lang(self, lang: str):
        if lang is None:
            return
        self.lang = lang

    def set_bandwidth(self, bandwidth: Union[str, int]):
        if bandwidth is None:
            return
        if isinstance(bandwidth, str):
            bandwidth = int(bandwidth)
        self.bandwidth = bandwidth

    def set_codecs(self, codecs: str):
        if codecs is None:
            return
        # https://chromium.googlesource.com/chromium/src/media/+/master/base/mime_util_internal.cc
        if re.match('avc(1|3)*', codecs):
            codecs = 'H264'
        if re.match('(hev|hvc)1*', codecs):
            codecs = 'H265'
        if re.match('vp(09|9)*', codecs):
            codecs = 'VP9'
        if codecs in ['wvtt', 'ttml', 'stpp']:
            codecs = codecs.upper()
        if AUDIO_CODECS.get(codecs) is not None:
            if 'AAC' in AUDIO_CODECS[codecs]:
                codecs = 'AAC'
            else:
                codecs = AUDIO_CODECS[codecs]
        self.codecs = codecs

    def set_resolution(self, width: str, height: str):
        if width is None or height is None:
            return
        self.resolution = f'{width}x{height}'
        self.skey += '_' + self.resolution

    def set_stream_type(self, stream_type: str):
        if stream_type is None:
            return
        stream_type, stream_suffix = stream_type.split('/')
        if stream_suffix == 'ttml+xml':
            stream_type = 'subtitle'
            self.suffix = '.ttml'
        elif stream_suffix == 'vtt':
            self.suffix = '.vtt'
            stream_type = 'subtitle'
        if stream_type == 'application':
            if self.codecs is None:
                return
            if self.codecs.lower() in ['wvtt', 'ttml', 'stpp']:
                stream_type = 'subtitle'
            else:
                return
        self.stream_type = stream_type
        if self.stream_type == 'audio':
            self.suffix = '.m4a'
