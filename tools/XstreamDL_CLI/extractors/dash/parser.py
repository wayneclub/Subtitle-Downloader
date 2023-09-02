import re
import math
from datetime import datetime, timezone
from typing import List, Dict, Union
from .mpd import MPD
from .handler import xml_handler
from .childs.adaptationset import AdaptationSet
from .childs.role import Role
from .childs.baseurl import BaseURL
from .childs.contentprotection import ContentProtection
from .childs.period import Period
from .childs.representation import Representation
from .childs.s import S
from .childs.segmentlist import SegmentList
from .childs.initialization import Initialization
from .childs.segmenturl import SegmentURL
from .childs.segmentbase import SegmentBaee
from .childs.segmenttemplate import SegmentTemplate
from .childs.segmenttimeline import SegmentTimeline

from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.models.base import BaseUri
from tools.XstreamDL_CLI.extractors.base import BaseParser
from tools.XstreamDL_CLI.extractors.dash.key import DASHKey
from tools.XstreamDL_CLI.extractors.dash.stream import DASHStream
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class DASHParser(BaseParser):
    def __init__(self, args: CmdArgs, uri_type: str):
        super(DASHParser, self).__init__(args, uri_type)
        self.is_live = False
        self.root = None  # type: MPD
        self.suffix = '.mpd'

    def fix_dash_base_url(self, previous_base_url: str, element: Union[MPD, Period, AdaptationSet, Representation]):
        '''
        BaseURL 可以是下面四个元素的子元素
        - MPD
        - Period
        - AdaptationSet
        - Representation

        根据多个渠道得到的BaseURL样本
        - 已有base_url路径上一级再拼接/all/ <BaseURL>../all/</BaseURL>
        - 已有base_url路径根路径拼接 <BaseURL>/12345/2145124</BaseURL>
        - 已有base_url路径常规拼接后续还需要拼接 <BaseURL>1280x720/</BaseURL>
        - 已有base_url路径常规拼接得到完整路径 <BaseURL>subtitles/TH/023719X0TH.vtt</BaseURL>
        - 已有base_url路径常规拼接得到完整路径 往往和SegmentBase搭配 <BaseURL>c0f671df-1314-4e9f-8aba-9ee42c26a69d_video_1.mp4</BaseURL>
        - 替换掉已有base_url 且通常有多个cdn <BaseURL serviceLocation="15802-Akamai" dvb:priority="3" dvb:weight="33">http://xxx.movetv.com/15802/live/PREM1/xxx/</BaseURL>

        每到一个层级都检查修正 修正后的base_url应当只适用于当前层级
        '''
        # logger.debug(f'previous_base_url {previous_base_url}')
        # 不管何时 previous_base_url 都应当以 http(s):// 开头
        if re.match(r'^https?://', previous_base_url) is None:
            assert False, 'unexcepted condition, report information to me'
        assert isinstance(element, (MPD, Period, AdaptationSet, Representation)
                          ), f'unexpected element type => {type(element)}'
        elements = element.find('BaseURL')  # type: List[BaseURL]
        # 当前层级子元素中没有BaseURL元素
        # 那么原来的base_url是什么 那当前层级的base_url就是什么
        if len(elements) == 0:
            return previous_base_url
        base_url_element = None  # type: BaseURL
        # 多个BaseURL则根据serviceLocation选择 否则选择第一个
        if len(elements) == 1:
            base_url_element = elements[0]
        else:
            # 没有指定 serviceLocation 则选第一个
            if not self.args.service:
                base_url_element = elements[0]
            else:
                # 如果BaseURL本身有serviceLocation 那么先尝试完全匹配
                for _element in elements:
                    if not _element.serviceLocation:
                        continue
                    if _element.serviceLocation == self.args.service:
                        base_url_element = _element
                        break
                if base_url_element is None:
                    # 不行再部分匹配
                    for _element in elements:
                        if not _element.serviceLocation:
                            continue
                        if self.args.service.lower() in _element.serviceLocation.lower():
                            base_url_element = _element
                            break
                if base_url_element is None:
                    # 还不行说明没有serviceLocation 那就选第一个
                    base_url_element = elements[0]
        # 先取内容
        base_url = base_url_element.innertext
        # 根据不同情况进行修正
        if re.match(r'^https?://', base_url):
            # 应当替换掉原有base_url
            return base_url
        if base_url.startswith('../'):
            # 对于这种情况应当去除末尾的/
            if previous_base_url.endswith('/'):
                previous_base_url = previous_base_url.rstrip('/')
            while base_url.startswith('../'):
                previous_base_url = '/'.join(previous_base_url.split("/")[:-1])
                base_url = base_url[3:]
            return previous_base_url + '/' + base_url
        if base_url.startswith('/'):
            items = previous_base_url.split('/')
            if len(items) >= 3:
                return '/'.join(items[:3]) + base_url
            else:
                # 最开始做过判断了 理论上不会走到这个分支 断言以防万一(...
                assert False, 'unexcepted condition, report information to me'
        if not previous_base_url.endswith('/'):
            previous_base_url += '/'
        return previous_base_url + base_url

    def parse(self, uri: str, content: str) -> List[DASHStream]:
        uri_item = self.parse_uri(uri)
        if uri_item is None:
            logger.error(f'parse {uri} failed')
            return []
        self.dump_content(uri_item.name, content, self.suffix)
        # 解析转换内容为期望的对象
        mpd = xml_handler(content)
        self.root = mpd
        # 检查是不是直播流
        if mpd.profiles == 'urn:mpeg:dash:profile:isoff-live:2011' and mpd.type != 'static':
            self.args.live = True
            self.is_live = True
        if self.args.live and self.is_live is False:
            logger.debug('detect current dash content is a living stream')
            self.is_live = True
        # 修正 MPD 节点的 BaseURL
        base_url = self.fix_dash_base_url(uri_item.base_url, mpd)
        return self.walk_period(mpd, uri_item.new_base_url(base_url))

    def walk_period(self, mpd: MPD, uri_item: BaseUri):
        periods = mpd.find('Period')  # type: List[Period]
        # 根据Period数量处理时长参数
        if len(periods) == 1 and periods[0].duration is None:
            # 当只存在一条流 且当前Period没有duration属性
            # 则使用mediaPresentationDuration作为当前Period的时长
            if hasattr(mpd, 'mediaPresentationDuration'):
                periods[0].duration = mpd.mediaPresentationDuration
            else:
                periods[0].duration = 0.0
        # 遍历处理periods
        streams = []
        for period in periods:
            # 修正 Period 节点的 BaseURL
            base_url = self.fix_dash_base_url(uri_item.base_url, period)
            _streams = self.walk_adaptationset(period, len(
                streams), uri_item.new_base_url(base_url))
            streams.extend(_streams)
        # 处理掉末尾的空分段
        for stream in streams:
            if stream.segments[-1].url == '':
                _ = stream.segments.pop(-1)
        # 合并流
        skey_stream = {}  # type: Dict[str, DASHStream]
        for stream in streams:
            if stream.skey in skey_stream:
                skey_stream[stream.skey].update(
                    stream, name_from_url=self.args.name_from_url)
            else:
                skey_stream[stream.skey] = stream
        streams = list(skey_stream.values())
        return streams

    def walk_adaptationset(self, period: Period, sindex: int, uri_item: BaseUri):
        # type: List[AdaptationSet]
        adaptationsets = period.find('AdaptationSet')
        streams = []
        for adaptationset in adaptationsets:
            # 修正 AdaptationSet 节点的 BaseURL
            base_url = self.fix_dash_base_url(uri_item.base_url, adaptationset)
            current_uri_item = uri_item.new_base_url(base_url)
            if adaptationset.mimeType == 'image/jpeg':
                logger.debug(
                    f'skip parse for AdaptationSet mimeType image/jpeg')
                continue
            representations = adaptationset.find(
                'Representation')  # type: List[Representation]
            if len(representations) > 0:
                _streams = self.walk_representation(
                    adaptationset, period, sindex + len(streams), current_uri_item)
            else:
                assert False, 'not implemented yet, report this mpd content to me'
                segmenttemplates = adaptationset.find(
                    'SegmentTemplate')  # type: List[SegmentTemplate]
                assert len(
                    segmenttemplates) == 1, 'plz report this mpd content to me'
                segmenttimelines = segmenttemplates[0].find(
                    'SegmentTimeline')  # type: List[SegmentTimeline]
                _streams = self.walk_s_v2(
                    segmenttimelines[0], adaptationset, period, sindex + len(streams), current_uri_item)
            streams.extend(_streams)
        return streams

    def walk_representation(self, adaptationset: AdaptationSet, period: Period, sindex: int, uri_item: BaseUri):
        '''
        每一个<Representation></Representation>都对应轨道的一/整段
        '''
        representations = adaptationset.find(
            'Representation')  # type: List[Representation]
        segmenttemplates = adaptationset.find(
            'SegmentTemplate')  # type: List[SegmentTemplate]
        streams = []
        for representation in representations:
            # 修正 Representation 节点的 BaseURL
            base_url = self.fix_dash_base_url(
                uri_item.base_url, representation)
            current_uri_item = uri_item.new_base_url(base_url)
            if self.args.log_level == 'DEBUG':
                logger.debug(f'current_base_url {current_uri_item.base_url}')
            stream = DASHStream(sindex, current_uri_item, self.args.save_dir)
            sindex += 1
            self.walk_contentprotection(adaptationset, stream)
            self.walk_contentprotection(representation, stream)
            # 给流设置属性
            stream.set_skey(adaptationset.id, representation.id)
            stream.set_lang(adaptationset.lang)
            stream.set_bandwidth(representation.bandwidth)
            if representation.codecs is None:
                stream.set_codecs(adaptationset.codecs)
            else:
                stream.set_codecs(representation.codecs)
            if representation.mimeType is None:
                stream.set_stream_type(adaptationset.mimeType)
            else:
                stream.set_stream_type(representation.mimeType)
            if representation.width is None or representation.height is None:
                stream.set_resolution(
                    adaptationset.width, adaptationset.height)
            else:
                stream.set_resolution(
                    representation.width, representation.height)
            # 针对字幕直链类型
            Roles = adaptationset.find('Role')  # type: List[Role]
            if stream.stream_type == '' and len(Roles) > 0:
                stream.set_stream_type(Roles[0].value)
            segmentlists = representation.find(
                'SegmentList')  # type: List[SegmentList]
            r_segmenttemplates = representation.find(
                'SegmentTemplate')  # type: List[SegmentTemplate]
            # 针对视频音频流处理 分情况生成链接
            if len(segmentlists) == 1:
                self.walk_segmentlist(
                    segmentlists[0], representation, period, stream)
            elif len(segmenttemplates) == 0:
                self.walk_segmenttemplate(representation, period, stream)
            elif len(segmenttemplates) == 1 and len(segmenttemplates[0].find('SegmentTimeline')) == 1:
                self.walk_segmenttimeline(
                    segmenttemplates[0], representation, period, stream)
            elif len(r_segmenttemplates) == 1 and len(r_segmenttemplates[0].find('SegmentTimeline')) == 1:
                self.walk_segmenttimeline(
                    r_segmenttemplates[0], representation, period, stream)
            elif len(segmenttemplates) == 1 and segmenttemplates[0].initialization is None:
                # tv-player.ap1.admint.biz live
                _segmenttemplates = representation.find('SegmentTemplate')
                if len(_segmenttemplates) != 1:
                    # AdaptationSet 的 SegmentTemplate 没有 initialization
                    # Representation 没有 SegmentTemplate 则跳过
                    continue
                # assert len(_segmenttemplates) == 1, '请报告出现此异常提示的mpd/report plz'
                segmenttemplate = segmenttemplates[0]
                _segmenttemplate = _segmenttemplates[0]
                if segmenttemplate.timescale is not None:
                    _segmenttemplate.timescale = segmenttemplate.timescale
                if segmenttemplate.duration is not None:
                    _segmenttemplate.duration = segmenttemplate.timescale
                self.generate_v1(period, representation.id,
                                 _segmenttemplate, stream)
            else:
                # SegmentTemplate 和多个 Representation 在同一级
                # 那么 SegmentTemplate 的时长参数等就是多个 Representation 的参数
                # 同一级的时候 只有一个 SegmentTemplate
                self.generate_v1(period, representation.id,
                                 segmenttemplates[0], stream)
            streams.append(stream)
        return streams

    def walk_segmentlist(self, segmentlist: SegmentList, representation: Representation, period: Period, stream: DASHStream):
        initializations = segmentlist.find(
            'Initialization')  # type: List[Initialization]
        has_initialization = False
        if len(initializations) == 1:
            has_initialization = True
            stream.set_init_url(initializations[0].sourceURL)
        segmenturls = segmentlist.find('SegmentURL')  # type: List[SegmentURL]
        for segmenturl in segmenturls:
            if segmenturl.media == '':
                # 通常就是一个整段
                continue
            stream.set_media_url(
                segmenturl.media, name_from_url=self.args.name_from_url)
        if has_initialization:
            interval = float(segmentlist.duration / segmentlist.timescale)
            stream.set_segments_duration(interval)

    def walk_contentprotection(self, representation: Representation, stream: DASHStream):
        ''' 流的加密方案 '''
        contentprotections = representation.find(
            'ContentProtection')  # type: List[ContentProtection]
        for contentprotection in contentprotections:
            # DASH流的解密通常是合并完整后一次解密
            # 不适宜每个分段单独解密
            # 那么这里就不用给每个分段设置解密key了
            # 而且往往key不好拿到 所以这里仅仅做一个存储
            stream.append_key(DASHKey(contentprotection))

    def walk_segmenttemplate(self, representation: Representation, period: Period, stream: DASHStream):
        baseurls = representation.find('BaseURL')  # type: List[BaseURL]
        segmentbases = representation.find(
            'SegmentBase')  # type: List[SegmentBaee]
        if len(segmentbases) == 1 and len(baseurls) == 1:
            if stream.base_url.startswith('http') or stream.base_url.startswith('/'):
                stream.set_init_url(stream.base_url)
            else:
                # set baseurls[0].innertext.strip() ?
                stream.set_init_url('../' + stream.base_url)
            # stream.set_segment_duration(-1)
            return
        segmenttemplates = representation.find(
            'SegmentTemplate')  # type: List[SegmentTemplate]
        # segmenttimelines = representation.find('SegmentTimeline') # type: List[SegmentTimeline]
        if len(segmenttemplates) != 1:
            # 正常情况下 这里应该只有一个SegmentTemplate
            # 没有就无法计算分段 则跳过
            # 不止一个可能是没见过的类型 提醒上报
            if len(segmenttemplates) > 1:
                logger.error('please report this DASH content.')
            else:
                # logger.warning('stream has no SegmentTemplate between Representation tag.')
                if stream.base_url.startswith('http'):
                    stream.set_init_url(stream.base_url)
            return
        if len(segmenttemplates[0].find('SegmentTimeline')) == 0:
            self.generate_v1(period, representation.id,
                             segmenttemplates[0], stream)
            return
        self.walk_segmenttimeline(
            segmenttemplates[0], representation, period, stream)

    def walk_segmenttimeline(self, segmenttemplate: SegmentTemplate, representation: Representation, period: Period, stream: DASHStream):
        segmenttimelines = segmenttemplate.find(
            'SegmentTimeline')  # type: List[SegmentTimeline]
        if len(segmenttimelines) != 1:
            if len(segmenttimelines) > 1:
                logger.error('please report this DASH content.')
            else:
                logger.warning(
                    'stream has no SegmentTimeline between SegmentTemplate tag.')
            return
        self.walk_s(segmenttimelines[0], segmenttemplate,
                    representation, period, stream)

    def walk_s_v2(self, segmenttimeline: SegmentTimeline, adaptationset: AdaptationSet, period: Period, sindex: int, uri_item: BaseUri):
        stream = DASHStream(sindex, uri_item, self.args.save_dir)
        stream.set_skey(adaptationset.id, None)
        sindex += 1
        return [stream]

    def walk_s(self, segmenttimeline: SegmentTimeline, st: SegmentTemplate, representation: Representation, period: Period, stream: DASHStream):
        init_url = st.get_url()
        if init_url is not None:
            if '$RepresentationID$' in init_url:
                init_url = init_url.replace(
                    '$RepresentationID$', representation.id)
            if '$Bandwidth$' in init_url:
                init_url = init_url.replace(
                    '$Bandwidth$', str(representation.bandwidth))
            if re.match('.*?as=audio_(.*?)\)', init_url):
                _lang = re.match('.*?as=audio_(.*?)\)', init_url).groups()[0]
                stream.set_lang(_lang)
            stream.set_init_url(init_url)
        else:
            # 这种情况可能是因为流是字幕
            pass
        target_r = 0  # type: int
        ss = segmenttimeline.find('S')  # type: List[S]
        if len(ss) > 0 and self.is_live and ss[0].t > 0:
            # 这个部分是修正 base_time
            # timeShiftBufferDepth => cdn max cache time for segments
            # newest available segment $Time$ should meet below condition
            # SegmentTimeline.S.t / timescale + (mpd.availabilityStartTime + Period.start) <= time.time()
            base_time = None  # type: int
            assert isinstance(self.root.availabilityStartTime,
                              float), 'report mpd to me'
            current_utctime = self.root.publishTime.timestamp() - self.args.live_utc_offset
            presentation_start = period.start - st.presentationTimeOffset / st.timescale + 30
            start_utctime = self.root.availabilityStartTime + presentation_start
            if self.args.log_level == 'DEBUG':
                logger.debug(
                    f'mpd.presentationTimeOffset {st.presentationTimeOffset} timescale {st.timescale}')
                logger.debug(
                    f'mpd.availabilityStartTime {self.root.availabilityStartTime} Period.start {period.start}')
                logger.debug(
                    f'start_utctime {start_utctime} current_utctime {current_utctime}')
            tmp_t = ss[0].t
            for s in ss:
                for number in range(s.r):
                    if (tmp_t + s.d) / st.timescale + start_utctime > current_utctime:
                        base_time = tmp_t
                        if self.args.log_level == 'DEBUG':
                            logger.debug(
                                f'set base_time {base_time} target_r {target_r}')
                        break
                    if target_r > 0:
                        tmp_t += s.d
                    target_r += 1
                if base_time:
                    break
            if base_time is None:
                logger.debug(
                    f'{representation.id} report mpd to me, maybe need wait {current_utctime - start_utctime - tmp_t / st.timescale}s')
            assert base_time is not None, f'{representation.id} report mpd to me, maybe need wait {current_utctime - start_utctime - tmp_t / st.timescale}s'
            # if base_time is None:
            #     base_time = ss[0].t
        elif ss[0].t > 0:
            base_time = ss[0].t
            logger.debug(f'ss[0].t > 0, set base_time {base_time}')
        else:
            base_time = 0
        # 如果 base_time 不为 0 即第一个 s.t 不为
        # 那么 time_offset 就不需要 即设置为 0
        time_offset = st.presentationTimeOffset if base_time == 0 else 0
        start_number = st.startNumber
        tmp_offset_r = 0
        total_segments_duration = 0.0
        for index, s in enumerate(ss):
            if self.args.multi_s and index > 0 and s.t > 0:
                base_time = s.t
            if st.timescale == 0:
                interval = 0
            else:
                interval = s.d / st.timescale
            if s.r == -1:
                _range = math.ceil(
                    (period.duration or self.root.mediaPresentationDuration) / interval)
            else:
                _range = s.r
            for number in range(_range):
                tmp_offset_r += 1
                if self.is_live and tmp_offset_r < target_r:
                    continue
                # 经过测试 对于直播流 应当计算时长来确定应该下载的分段
                # 因为无法通过比较两轮的url来排除已经下载的分段 通过url比较会导致重复下载
                # 根据标准 这里与 minBufferTime 或者 minimumUpdatePeriod 比较都可以 浏览器是后者 保持一致
                if self.is_live and total_segments_duration > self.root.minimumUpdatePeriod:
                    break
                total_segments_duration += interval
                media_url = st.get_media_url()
                if '$Bandwidth$' in media_url:
                    media_url = media_url.replace(
                        '$Bandwidth$', str(representation.bandwidth))
                if '$Number$' in media_url:
                    media_url = media_url.replace(
                        '$Number$', str(start_number))
                    start_number += 1
                if re.match('.*?(\$Number%(.+?)\$)', media_url):
                    old, fmt = re.match(
                        '.*?(\$Number(%.+?)\$)', media_url).groups()
                    new = fmt % start_number
                    media_url = media_url.replace(old, new)
                    start_number += 1
                if '$RepresentationID$' in media_url:
                    media_url = media_url.replace(
                        '$RepresentationID$', representation.id)
                if '$Time$' in media_url:
                    fmt_time = time_offset + base_time
                    stream.set_segment_fmt_time(fmt_time)
                    media_url = media_url.replace('$Time$', str(fmt_time))
                    time_offset += s.d
                stream.set_segment_duration(interval)
                stream.set_media_url(
                    media_url, name_from_url=self.args.name_from_url)

    def generate_v1(self, period: Period, rid: str, st: SegmentTemplate, stream: DASHStream):
        init_url = st.get_url()
        if '$RepresentationID$' in init_url:
            init_url = init_url.replace('$RepresentationID$', rid)
        stream.set_init_url(init_url)
        if st.timescale == 0:
            interval = st.duration
        else:
            interval = float(int(st.duration) / int(st.timescale))
        if self.is_live:
            # 对于直播流来说应该有两个线程 一个刷新分段信息 一个负责下载 但是不想大改 就这样用吧
            # 这样带来的问题是，下载速度要快且稳定 不然容易丢失分段
            current_utctime = datetime.now(
                timezone.utc).timestamp() - self.args.live_utc_offset + 30
            presentation_start = period.start - st.presentationTimeOffset / st.timescale + 30
            start_utctime = self.root.availabilityStartTime + presentation_start
            number_start = math.ceil(
                (self.root.publishTime.timestamp() - start_utctime) / interval)
            max_repeat = math.ceil(self.root.minimumUpdatePeriod / interval)
            repeat = 0
            for i in range(max_repeat):
                repeat += 1
                if (number_start + repeat) * interval + start_utctime > current_utctime:
                    break
        else:
            number_start = int(st.startNumber)
            repeat = math.ceil(period.duration / interval)
        for number in range(number_start, repeat + number_start):
            media_url = st.get_media_url()
            if '$Number$' in media_url:
                media_url = media_url.replace('$Number$', str(number))
            if re.match('.*?(\$Number%(.+?)\$)', media_url):
                old, fmt = re.match(
                    '.*?(\$Number(%.+?)\$)', media_url).groups()
                new = fmt % number
                media_url = media_url.replace(old, new)
            if '$RepresentationID$' in media_url:
                media_url = media_url.replace('$RepresentationID$', rid)
            if self.is_live and '$Time$' in media_url:
                fmt_time = number * st.duration
                stream.set_segment_fmt_time(fmt_time)
                media_url = media_url.replace('$Time$', str(fmt_time))
            stream.set_media_url(
                media_url, name_from_url=self.args.name_from_url)
        stream.set_segments_duration(interval)
