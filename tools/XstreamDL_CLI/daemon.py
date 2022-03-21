import time
from typing import List
from pathlib import Path
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.extractor import Extractor
from tools.XstreamDL_CLI.downloader import Downloader
from tools.XstreamDL_CLI.models.stream import Stream
from tools.XstreamDL_CLI.extractors.hls.stream import HLSStream
from tools.XstreamDL_CLI.extractors.dash.stream import DASHStream
from tools.XstreamDL_CLI.extractors.dash.parser import DASHParser
from tools.XstreamDL_CLI.extractors.dash.childs.location import Location
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class Daemon:

    def __init__(self, args: CmdArgs):
        self.args = args
        self.exit = False

    def daemon(self):
        '''
        - 解析
        - 下载
        - 合并
        '''
        extractor = Extractor(self.args)
        streams = extractor.fetch_metadata(self.args.URI[0])
        if self.args.live is False:
            return Downloader(self.args).download_streams(streams)
        else:
            return self.live_record(extractor, streams)

    def live_record(self, extractor: Extractor, streams: List[Stream]):
        '''
        - 第一轮解析 判断类型
        - 选择流 交给下一个函数具体下载-刷新-下载...
        - TODO
        -   提供录制时长设定
        '''
        if isinstance(streams[0], DASHStream):
            self.live_record_dash(extractor, streams)
        if isinstance(streams[0], HLSStream):
            self.live_record_hls(extractor, streams)
        # assert False, f'unsupported live stream type {type(streams[0])}'

    def live_record_dash(self, extractor: Extractor, streams: List[DASHStream]):
        '''
        dash直播流
        重复拉取新的mpd后
        判断是否和之前的重复关键在于url的path部分是不是一样的
        也就是说 文件是不是一个
        那么主要逻辑如下
        - 再次解析 这一轮解析的时候 select 复用第一轮的选择 用skey来判断
        - 判断合并 下载已经解析好的分段
        - 再次解析 再次下载 直到满足结束条件
        Q 为何先再次解析而不是先下载完第一轮解析的分段再下载
        A 第一轮解析时有手动选择流的过程 而dash流刷新时间一般都很短 往往只有几秒钟 所以最好是尽快拉取一次最新的mpd
        Q 为什么不拉取新mpd单独开一个线程
        A 下载的时候很可能会占满网速 个人认为循环会好一点
        Q 万一下载卡住导致mpd刷新不及时怎么办
        A 还没有想好 不过这种情况概率蛮小的吧... 真的发生了说明你的当前网络不适合录制
        '''
        # assert False, 'not support dash live stream, wait plz'
        # 再次解析 优先使用 Location 作为要刷新的目标链接
        # 因为有的直播流 Location 会比用户填写的链接多一些具体标识 比如时间 或者token
        parser = extractor.parser  # type: DASHParser
        locations = parser.root.find('Location')  # type: List[Location]
        if len(locations) == 1:
            next_mpd_url: str = locations[0].innertext.strip()
        else:
            next_mpd_url = self.args.URI[0]
        if '://' not in next_mpd_url:
            if Path(next_mpd_url).is_file() or Path(next_mpd_url).is_dir():
                assert False, 'not support dash live stream for file/folder type, because cannot refresh'
        logger.info(f'refresh link {next_mpd_url}')
        # 初始化下载器
        downloader = Downloader(self.args)
        # 获取用户选择的流的skey
        skeys = downloader.do_select(streams)
        if len(skeys) == 0:
            return
        refresh_interval = self.args.live_refresh_interval
        last_time = time.time()
        while True:
            # 刷新间隔时间检查
            if time.time() - last_time < refresh_interval:
                time.sleep(0.5)
                continue
            last_time = time.time()
            # 复用 extractor 再次解析
            # 这里不应该是文件或者文件夹 当然第一轮可以是链接和文件
            next_streams = extractor.fetch_metadata(next_mpd_url)
            # 合并下载分段信息
            self.streams_extend(streams, next_streams, skeys)
            # 下载分段
            downloader.download_streams(streams, selected=skeys)
            # 检查是不是主动退出了
            if downloader.terminate:
                logger.debug(f'downloader terminated break')
                break
            # 继续循环
        downloader.try_concat_streams(streams, skeys)

    def live_record_hls(self, extractor: Extractor, streams: List[HLSStream]):
        '''
        hls直播流
        '''
        assert False, 'not support hls live stream, wait plz'

    def streams_extend(self, streams: List[DASHStream], next_streams: List[DASHStream], skeys: List[str]):
        _streams = dict((stream.get_skey(), stream) for stream in streams)
        _next_streams = dict((stream.get_skey(), stream)
                             for stream in next_streams)
        for skey in skeys:
            _stream = _streams.get(skey)  # type: DASHStream
            _next_stream = _next_streams.get(skey)  # type: DASHStream
            if _stream is None or _next_stream is None:
                continue
            # 对于新增的分段 认为默认有init分段
            _stream.live_segments_extend(_next_stream.segments, has_init=True,
                                         name_from_url=self.args.name_from_url, compare_with_url=self.args.compare_with_url)
