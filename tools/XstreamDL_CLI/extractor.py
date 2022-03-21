import asyncio
import platform
from typing import List
from pathlib import Path
from aiohttp.connector import TCPConnector
from aiohttp import ClientSession, ClientResponse
from aiohttp_socks import ProxyConnector
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.models.stream import Stream
from tools.XstreamDL_CLI.extractors.hls.parser import HLSParser
from tools.XstreamDL_CLI.extractors.hls.stream import HLSStream
from tools.XstreamDL_CLI.extractors.dash.parser import DASHParser
from tools.XstreamDL_CLI.extractors.dash.stream import DASHStream
from tools.XstreamDL_CLI.extractors.mss.parser import MSSParser
from tools.XstreamDL_CLI.extractors.mss.stream import MSSStream
from tools.XstreamDL_CLI.util.texts import t_msg

from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class Extractor:
    '''
    请求DASH/HLS链接内容，也就是下载元数据
    或者读取含有元数据的文件
    或者读取含有多个元数据文件的文件夹
    最终得到一个Stream（流）对象供Downloader（下载器）下载
    '''

    def __init__(self, args: CmdArgs):
        self.args = args
        self.parser = None

    def load_raw2text(self, data: bytes):
        raw_text = None  # type: str
        try:
            raw_text = data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                raw_text = data.decode('utf-16')
            except Exception as e:
                logger.error(f'load_raw2text failed', exc_info=e)
        return raw_text

    def fetch_metadata(self, uri: str, parent_stream: Stream = None):
        '''
        从链接/文件/文件夹等加载内容 解析metadata
        '''
        if uri.startswith('http://') or uri.startswith('https://') or uri.startswith('ftp://'):
            if platform.system() == 'Windows':
                asyncio.set_event_loop_policy(
                    asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.get_event_loop()
            return self.raw2streams('url', *loop.run_until_complete(self.fetch(uri)), parent_stream)
        if '\\' in uri:
            _file_name = uri.split('\\')[-1]
        elif '/' in uri:
            _file_name = uri.split('/')[-1]
        else:
            _file_name = uri
        illegal_symbols = ["\\", "/", ":", "：", "*",
                           "?", "\"", "<", ">", "|", "\r", "\n", "\t"]
        is_illegal_path = True
        for illegal_symbol in illegal_symbols:
            if illegal_symbol in _file_name:
                is_illegal_path = False
                break
        if is_illegal_path is False:
            return
        if Path(uri).exists() is False:
            return
        if Path(uri).is_file():
            return self.raw2streams('path', uri, self.load_raw2text(Path(uri).read_bytes()), parent_stream)
        if Path(uri).is_dir() is False:
            return
        streams = []
        for path in Path(uri).iterdir():
            _streams = self.raw2streams(
                'path', path.name, self.load_raw2text(path.read_bytes()), parent_stream)
            if _streams is None:
                continue
            streams.extend(_streams)
        return streams

    async def fetch(self, url: str) -> str:
        if self.args.proxy != '':
            connector = ProxyConnector.from_url(self.args.proxy, ssl=False)
        else:
            connector = TCPConnector(ssl=False)
        async with ClientSession(connector=connector) as client:  # type: ClientSession
            # type: ClientResponse
            async with client.get(url, headers=self.args.headers) as resp:
                return str(resp.url), self.load_raw2text(await resp.read())

    def raw2streams(self, uri_type: str, uri: str, content: str, parent_stream: Stream) -> List[Stream]:
        '''
        解析解码后的返回结果
        '''
        if not content:
            return []
        if content.startswith('#EXTM3U'):
            return self.parse_as_hls(uri_type, uri, content, parent_stream)
        elif '<MPD' in content and '</MPD>' in content:
            return self.parse_as_dash(uri_type, uri, content, parent_stream)
        elif '<SmoothStreamingMedia' in content and '</SmoothStreamingMedia>' in content:
            return self.parse_as_mss(uri_type, uri, content, parent_stream)
        else:
            logger.warning(t_msg.cannot_get_stream_metadata)
            return []

    def parse_as_hls(self, uri_type: str, uri: str, content: str, parent_stream: HLSStream = None) -> List[HLSStream]:
        _streams = HLSParser(self.args, uri_type).parse(
            uri, content, parent_stream)
        streams = []
        for stream in _streams:
            # 针对master类型加载详细内容
            if stream.tag != '#EXT-X-STREAM-INF' and stream.tag != '#EXT-X-MEDIA':
                streams.append(stream)
                continue
            if self.args.hide_load_metadata:
                logger.debug(
                    f'Load {stream.tag} metadata from -> {stream.origin_url}')
            else:
                logger.info(
                    f'Load {stream.tag} metadata from -> {stream.origin_url}')
            new_streams = self.fetch_metadata(
                stream.origin_url, parent_stream=stream)
            if new_streams is None:
                continue
            if len(new_streams) == 1:
                new_streams[0].patch_stream_info(stream)
            streams.extend(new_streams)
        # 在全部流解析完成后 再处理key
        for stream in streams:
            stream.try_fetch_key(self.args)
        return streams

    def parse_as_dash(self, uri_type: str, uri: str, content: str, parent_stream: DASHStream = None) -> List[DASHStream]:
        self.parser = DASHParser(self.args, uri_type)
        streams = self.parser.parse(uri, content)
        return streams

    def parse_as_mss(self, uri_type: str, uri: str, content: str, parent_stream: MSSStream = None) -> List[MSSStream]:
        streams = MSSParser(self.args, uri_type).parse(uri, content)
        return streams
