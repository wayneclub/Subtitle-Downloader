from typing import List
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.extractors.base import BaseParser
from tools.XstreamDL_CLI.extractors.hls.ext.xkey import XKey
from tools.XstreamDL_CLI.extractors.hls.stream import HLSStream
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class HLSParser(BaseParser):
    def __init__(self, args: CmdArgs, uri_type: str):
        super(HLSParser, self).__init__(args, uri_type)
        self.suffix = '.m3u8'

    def parse(self, uri: str, content: str, parent_stream: HLSStream) -> List[HLSStream]:
        uri_item = self.parse_uri(uri)
        if uri_item is None:
            logger.error(f'parse {uri} failed')
            return []
        self.dump_content(uri_item.name, content, self.suffix)
        streams = []
        sindex = 0
        stream = HLSStream(sindex, uri_item, self.args.save_dir, parent_stream)
        stream.set_origin_url(home_url=uri_item.home_url,
                              base_url=uri_item.base_url, uri=uri)
        lines = [line.strip() for line in content.split('\n')]
        offset = 0
        last_segment_xkey = None  # type: XKey
        content_is_master_type = False
        last_segment_has_xkey = False
        do_not_append_at_end_list_tag = False
        while offset < len(lines):
            segment = stream.segments[-1]
            line = lines[offset]
            line = line.replace(', ', ',')
            # 分段标准tag参考 -> https://tools.ietf.org/html/rfc8216#section-4.3.2
            if line == '':
                pass
            elif line.startswith('#EXTM3U'):
                stream.set_tag('#EXTM3U')
            elif line.startswith('#EXT-X-VERSION'):
                pass
            elif line.startswith('#EXT-X-KEY'):
                if offset > 0 and lines[offset - 1].startswith('#EXT-X-'):
                    # 把这个位置的#EXT-X-KEY认为是全局的
                    stream.set_key(uri_item.home_url, uri_item.base_url, line)
                else:
                    segment.set_key(uri_item.home_url, uri_item.base_url, line)
                    if last_segment_has_xkey is False:
                        last_segment_has_xkey = True
                        last_segment_xkey = segment.get_xkey()
            elif line.startswith('#EXT-X-SESSION-KEY'):
                # 某些网站的
                pass
            elif line.startswith('#EXT-X-I-FRAMES-ONLY'):
                pass
            elif line.startswith('#EXT-X-INDEPENDENT-SEGMENTS'):
                pass
            elif line.startswith('#EXT-X-ALLOW-CACHE'):
                pass
            elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                pass
            elif line.startswith('#EXT-X-PROGRAM-DATE-TIME'):
                # 根据spec 该标签指明的是第一个分段绝对日期/时间
                stream.set_xprogram_date_time(line)
            elif line.startswith('#EXT-X-DATERANGE'):
                # 按设计应该把这个标签认为是一个Stream的属性
                stream.set_daterange(line)
            elif line.startswith('#EXT-X-TARGETDURATION'):
                pass
            elif line.startswith('#EXT-X-PLAYLIST-TYPE'):
                pass
            elif line.startswith('#EXT-X-DISCONTINUITY'):
                if self.args.dont_split_discontinuity:
                    pass
                else:
                    # 此标签后面的分段都认为是一个新的Stream 直到结束或下一个相同标签出现
                    # 对于优酷 根据特征字符匹配 移除不需要的Stream 然后将剩余的Stream合并
                    sindex += 1
                    _xkey = stream.xkey
                    _bakcup_xkey = stream.bakcup_xkey
                    streams.append(stream)
                    stream = HLSStream(
                        sindex, uri_item, self.args.save_dir, parent_stream)
                    stream.set_origin_url(
                        uri_item.home_url, uri_item.base_url, uri)
                    stream.set_xkey(_xkey)
                    stream.set_bakcup_xkey(_bakcup_xkey)
                    stream.set_tag('#EXT-X-DISCONTINUITY')
            elif line.startswith('#EXT-X-MAP'):
                segment.set_map_url(uri_item.home_url, uri_item.base_url, line)
                stream.set_map_flag()
                stream.append_segment()
            elif line.startswith('#EXT-X-TIMESTAMP-MAP'):
                pass
            elif line.startswith('#USP-X-TIMESTAMP-MAP'):
                pass
            elif line.startswith('#EXTINF'):
                segment.set_duration(line)
            elif line.startswith('#EXT-X-PRIVINF'):
                segment.set_privinf(line)
            elif line.startswith('#EXT-X-BYTERANGE'):
                segment.set_byterange(line)
            elif line.startswith('#EXT-X-BITRATE'):
                pass
            elif line.startswith('#EXT-X-ENDLIST'):
                pass
            elif line.startswith('#EXT-X-MEDIA'):
                # 外挂媒体 视为单独的一条流
                if "URI=" in line:
                    sindex += 1
                    stream.set_tag('#EXT-X-MEDIA')
                    stream.set_media(uri_item.home_url,
                                     uri_item.base_url, line)
                    content_is_master_type = True
                    streams.append(stream)
                    stream = HLSStream(
                        sindex, uri_item, self.args.save_dir, parent_stream)
            # elif line.startswith('#EXT-X-STREAM-INF'):
            elif line.startswith('#EXT-X-') and 'STREAM-INF' in line:
                stream.set_tag('#EXT-X-STREAM-INF')
                stream.set_xstream_inf(line)
                content_is_master_type = True
                if stream.xstream_inf.uri is None:
                    pass
                else:
                    # handle for #EXT-X-I-FRAME-STREAM-INF
                    sindex += 1
                    do_not_append_at_end_list_tag = True
                    stream.set_origin_url(
                        uri_item.home_url, uri_item.base_url, stream.xstream_inf.uri)
                    streams.append(stream)
                    stream = HLSStream(
                        sindex, uri_item, self.args.save_dir, parent_stream)
            elif line.startswith('#'):
                if line.startswith('## Generated with https://github.com/google/shaka-packager'):
                    pass
                elif line.startswith('## Created with Unified Streaming Platform'):
                    pass
                else:
                    logger.warning(f'unknown TAG, skip\n\t{line}')
            else:
                # 进入此处 说明这一行没有任何已知的#EXT标签 也就是具体媒体文件的链接
                if offset > 0 and lines[offset - 1].startswith('#EXT-X-BYTERANGE'):
                    segment.set_xkey(last_segment_has_xkey, last_segment_xkey)
                    segment.set_url(uri_item.home_url, uri_item.base_url, line)
                    stream.append_segment()
                elif offset > 0 and lines[offset - 1].startswith('#EXT-X-PRIVINF'):
                    segment.set_xkey(last_segment_has_xkey, last_segment_xkey)
                    segment.set_url(uri_item.home_url, uri_item.base_url, line)
                    stream.append_segment()
                elif offset > 0 and lines[offset - 1].startswith('#EXTINF') or lines[offset - 1].startswith('#EXT-X-BITRATE'):
                    segment.set_xkey(last_segment_has_xkey, last_segment_xkey)
                    segment.set_url(uri_item.home_url, uri_item.base_url, line)
                    stream.append_segment()
                elif offset > 0 and lines[offset - 1].startswith('#EXT-X-') and 'STREAM-INF' in lines[offset - 1]:
                    sindex += 1
                    stream.set_url(uri_item.home_url, uri_item.base_url, line)
                    streams.append(stream)
                    stream = HLSStream(
                        sindex, uri_item, self.args.save_dir, parent_stream)
                    do_not_append_at_end_list_tag = True
                else:
                    logger.warning(f'unknow what to do here ->\n\t{line}')
            offset += 1
        if do_not_append_at_end_list_tag is False:
            streams.append(stream)
        # 下面的for循环中stream/segment是浅拷贝
        _stream_paths = []
        _streams = []  # type: List[HLSStream]
        for stream in streams:
            # 去重
            if stream.tag == '#EXT-X-STREAM-INF':
                stream_path = stream.get_path()
                if stream_path in _stream_paths:
                    continue
                elif stream_path == '':
                    # 文件类型
                    pass
                else:
                    _stream_paths.append(stream_path)
            # 处理掉末尾空的分段
            if stream.segments[-1].url == '':
                _ = stream.segments.pop(-1)
            # 过滤掉广告片段
            _segments = []
            for segment in stream.segments:
                if self.args.ad_keyword == '':
                    _segments.append(segment)
                elif self.args.ad_keyword not in segment.url:
                    _segments.append(segment)
            stream.segments = _segments
            # 保留过滤掉广告片段分段数大于0的Stream
            if len(stream.segments) > 0 or stream.tag == '#EXT-X-STREAM-INF' or stream.tag == '#EXT-X-MEDIA':
                _streams.append(stream)
        # if content_is_master_type is False and len(_streams) > 1:
        if content_is_master_type is False and len(_streams) > 1:
            streams = []
            # 合并去除#EXT-X-DISCONTINUITY后剩下的Stream
            stream = _streams[0]
            for _stream in _streams[1:]:
                # 一条流中有map时不参与合并
                if _stream.has_map_segment:
                    streams.append(stream)
                    stream = _stream
                    continue
                else:
                    stream.segments_extend(
                        _stream.segments, name_from_url=self.args.name_from_url)
            streams.append(stream)
            _streams = streams
        return _streams
