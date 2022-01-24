import base64
from logging import Logger
from typing import List
from pathlib import Path
from tools.xstream.cmdargs import CmdArgs
from tools.xstream.models.base import BaseUri
from tools.xstream.models.stream import Stream
from tools.xstream.extractors.hls.segment import HLSSegment
from tools.xstream.extractors.hls.ext.xkey import XKey
from tools.xstream.extractors.hls.ext.xmedia import XMedia
from tools.xstream.extractors.hls.ext.xdaterange import XDateRange
from tools.xstream.extractors.hls.ext.xstream_inf import XStreamInf
from tools.xstream.extractors.hls.ext.xprogram_date_time import XProgramDateTime


class HLSStream(Stream):
    '''
    自适应流的具体实现，HLS/DASH等，为了下载对应的流，
    每一条流应当具有以下基本属性：
    - 名称
    - 分段链接列表
    - 分辨率
    - 码率
    - 时长
    - 编码
    一些可选的属性
    - 语言
    '''

    def __init__(self, index: int, uri_item: BaseUri, save_dir: Path, parent_stream: 'HLSStream'):
        super(HLSStream, self).__init__(index, uri_item, save_dir)
        self.model = 'hls'
        self.segments = []  # type: List[HLSSegment]
        # <------对于HLS类型的流额外的属性------>
        self.xkey = None
        self.program_id = None  # type: int
        self.average_bandwidth = None  # type: int
        self.size = None  # type: int
        self.quality = None  # type: str
        self.has_map_segment = False
        self.xmedias = []  # type: List[XMedia]
        self.xstream_inf = None  # type: XStreamInf
        self.bakcup_xkey = None
        self.group_id = ''
        # 如果parent_stream不为空 那么将一些属性进行赋值
        if parent_stream is not None:
            self.fps = parent_stream.fps
            self.lang = parent_stream.lang
            self.group_id = parent_stream.group_id
            self.codecs = parent_stream.codecs
            self.bandwidth = parent_stream.bandwidth
            self.resolution = parent_stream.resolution
            self.stream_type = parent_stream.stream_type
        # 初始化默认设定一个分段
        self.append_segment()

    def set_stream_lang(self, lang: str):
        if not lang:
            return
        self.lang = lang

    def set_stream_group_id(self, group_id: str):
        if not group_id:
            return
        self.group_id = group_id

    def set_stream_type(self, stream_type: str):
        ''' #EXT-X-MEDIA 会表明流类型 '''
        self.stream_type = stream_type
        if self.stream_type == 'audio':
            self.suffix = '.m4a'

    def get_name(self):
        if self.stream_type != '':
            base_name = f'{self.name}_{self.stream_type}'
        else:
            base_name = self.name
        if self.resolution != '':
            base_name += f'_{self.resolution}'
        if self.lang != '':
            base_name += f'_{self.lang}'
        if self.group_id != '':
            base_name += f'_{self.group_id}'
        if self.bandwidth is not None:
            base_name += f'_{self.bandwidth / 1000:.2f}kbps'
        return base_name

    def patch_stream_info(self, stream: 'HLSStream'):
        if stream.codecs is not None:
            self.codecs = stream.codecs
        if stream.resolution != '':
            self.resolution = stream.resolution
        if stream.lang != '':
            self.lang = stream.lang
        if stream.fps is not None:
            self.fps = stream.fps
        if stream.bandwidth is not None:
            self.bandwidth = stream.bandwidth

    def set_name(self, name: str):
        self.name = name
        return self

    def set_tag(self, tag: str):
        self.tag = tag

    def set_map_flag(self):
        self.has_map_segment = True
        self.name += f'_{self.index}'
        self.save_dir = (self.save_dir.parent / self.name).resolve()
        for segment in self.segments:
            segment.set_folder(self.save_dir)

    def append_segment(self):
        '''
        新增一个分段
        '''
        index = len(self.segments)
        if self.has_map_segment:
            index -= 1
        segment = HLSSegment().set_index(index).set_folder(self.save_dir)
        self.segments.append(segment)

    def try_fetch_key(self, args: CmdArgs, logger: Logger):
        '''
        在解析过程中 已经设置了key的信息了
        但是没有请求key 这里是独立加载key的部分
        放在这个位置的原因是
            - 解析过程其实很短，没必要在解析时操作
            - 解析后还有合并流的过程
        所以最佳的方案是在解析之后再进行key的加载
        '''
        custom_xkey = XKey()
        if args.b64key is not None:
            _key = base64.b64decode(args.b64key.encode('utf-8'))
            custom_xkey.set_key(_key)
            if args.hexiv is not None:
                custom_xkey.set_iv(args.hexiv)
        if self.xkey is None:
            if args.b64key:
                # 如果解析后没有密钥相关信息
                # 而命令行又指定了 也进行设定
                self.set_segments_key(custom_xkey)
            return
        if self.xkey.method and self.xkey.method.upper() in ['SAMPLE-AES', 'SAMPLE-AES-CTR']:
            return
        if self.xkey.load(args, custom_xkey, logger) is True:
            logger.info(
                f'm3u8 key loaded\nmethod => {self.xkey.method}\nkey    => {self.xkey.key}\niv     => {self.xkey.iv}')
            self.set_segments_key(self.xkey)

    def set_segments_key(self, xkey: XKey):
        '''
        和每个分段的key对比 设定对应的解密信息
        '''
        self.xkey = xkey
        for segment in self.segments:
            segment.xkey = xkey

    def set_xkey(self, xkey: XKey):
        self.xkey = xkey

    def set_bakcup_xkey(self, bakcup_xkey: XKey):
        self.bakcup_xkey = bakcup_xkey

    def set_xstream_inf(self, line: str):
        self.xstream_inf = XStreamInf().set_attrs_from_line(line)
        if self.xstream_inf is not None:
            self.fps = self.xstream_inf.fps
            self.codecs = self.xstream_inf.codecs
            self.bandwidth = self.xstream_inf.bandwidth
            self.resolution = self.xstream_inf.resolution
            self.stream_type = self.xstream_inf.streamtype

    def get_path(self):
        ''' 某些m3u8会有重复的 例如D+ 这里辅助去重 '''
        # return self.origin_url.split('?', maxsplit=1)[0].split('/')[-1]
        return self.origin_url.split('?', maxsplit=1)[0].split('/', maxsplit=3)[-1:]

    def set_url(self, home_url: str, base_url: str, line: str):
        if line.startswith('http://') or line.startswith('https://') or line.startswith('ftp://'):
            self.origin_url = line
        elif line.startswith('/'):
            self.origin_url = f'{home_url}{line}'
        else:
            self.origin_url = f'{base_url}/{line}'

    def set_key(self, home_url: str, base_url: str, line: str):
        xkey = XKey().set_attrs_from_line(home_url, base_url, line)
        if xkey is None:
            return
        if self.xkey is None:
            self.xkey = xkey
        else:
            self.bakcup_xkey = xkey

    def set_media(self, home_url: str, base_url: str, line: str):
        xmedia = XMedia()
        xmedia.set_attrs_from_line(line)
        xmedia.uri = self.set_origin_url(home_url, base_url, xmedia.uri)
        self.set_stream_lang(xmedia.language)
        self.set_stream_group_id(xmedia.group_id)
        self.set_stream_type(xmedia.type)
        self.xmedias.append(xmedia)

    def set_origin_url(self, home_url: str, base_url: str, uri: str):
        # 某些标签 应该被视作一个新的Stream 所以要设置其对应的原始链接
        if uri.startswith('http://') or uri.startswith('https://') or uri.startswith('ftp://'):
            self.origin_url = uri
        elif uri.startswith('/'):
            self.origin_url = f'{home_url}{uri}'
            # 更新 base_url
            self.base_url = self.origin_url.split(
                '?', maxsplit=1)[0][::-1].split('/', maxsplit=1)[-1][::-1]
        else:
            self.origin_url = f'{base_url}/{uri}'
            # 更新 base_url
            self.base_url = self.origin_url.split(
                '?', maxsplit=1)[0][::-1].split('/', maxsplit=1)[-1][::-1]
        return self.origin_url

    def set_daterange(self, line: str):
        self.xdaterange = XDateRange().set_attrs_from_line(line)

    def set_xprogram_date_time(self, line: str):
        self.xprogram_date_time = XProgramDateTime().set_attrs_from_line(line)
