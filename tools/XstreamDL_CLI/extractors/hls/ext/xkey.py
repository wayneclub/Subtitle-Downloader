import asyncio
import platform
from aiohttp_socks import ProxyConnector
from aiohttp import ClientSession, ClientResponse
from aiohttp.connector import TCPConnector

from .x import X
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')

DEFAULT_IV = '0' * 32


class XKey(X):
    '''
    一组加密参数
    - METHOD
        - AES-128
        - SAMPLE-AES
    - URI
        - data:text/plain;base64,...
        - skd://...
    - IV
        - 0x/0X...
    - KEYFORMAT
        - urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed
        - com.apple.streamingkeydelivery
    '''

    def __init__(self):
        super(XKey, self).__init__('#EXT-X-KEY')
        self.method = 'AES-128'  # type: str
        self.uri = None  # type: str
        self.key = b''  # type: bytes
        self.keyid = None  # type: str
        self.iv = DEFAULT_IV  # type: str
        self.keyformatversions = None  # type: str
        self.keyformat = None  # type: str
        self.known_attrs = {
            'METHOD': 'method',
            'URI': 'uri',
            'KEYID': 'keyid',
            'IV': 'iv',
            'KEYFORMATVERSIONS': 'keyformatversions',
            'KEYFORMAT': 'keyformat',
        }

    def set_key(self, key: bytes):
        self.key = key
        return self

    def set_iv(self, iv: str):
        if iv is None:
            return
        self.iv = iv
        return self

    def set_attrs_from_line(self, home_url: str, base_url: str, line: str):
        '''
        key的链接可能不全 用home_url或base_url进行补齐 具体处理后面做
        '''
        line = line.replace('MEATHOD', 'METHOD')
        super(XKey, self).set_attrs_from_line(line)
        key_type, self.uri = self.gen_hls_key_uri(home_url, base_url)
        if self.iv.lower().startswith('0x'):
            self.iv = self.iv[2:]
        return self

    def gen_hls_key_uri(self, home_url: str, base_url: str):
        '''
        解析时 不具体调用这个函数 需要的地方再转换
        data:text/plain;base64,AAAASnBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAACoSEKg079lX5xeK9g/zZPwXENESEKg079lX5xeK9g/zZPwXENFI88aJmwY=
        skd://a834efd957e7178af60ff364fc1710d1
        '''
        if self.uri is None:
            return '', self.uri
        if self.uri.startswith('data:text/plain;base64,'):
            return 'base64', self.uri.split(',', maxsplit=1)[-1]
        elif self.uri.startswith('skd://'):
            return 'skd', self.uri.split('/', maxsplit=1)[-1]
        elif self.uri.startswith('http'):
            return 'http', self.uri
        elif self.uri.startswith('/'):
            return 'http', home_url + self.uri
        else:
            return 'http', base_url + '/' + self.uri

    async def fetch(self, url: str, args: CmdArgs) -> bytes:
        if args.proxy != '':
            connector = ProxyConnector.from_url(args.proxy, ssl=False)
        else:
            connector = TCPConnector(ssl=False)
        async with ClientSession(connector=connector) as client:  # type: ClientSession
            async with client.get(url, headers=args.headers) as resp:  # type: ClientResponse
                return await resp.content.read()

    def load(self, args: CmdArgs, custom_xkey: 'XKey'):
        '''
        如果custom_xkey存在key 那么覆盖解析结果中的key
        并且不进行请求key的动作 同时覆盖iv 如果有自定义iv的话
        '''
        if custom_xkey.iv != DEFAULT_IV:
            self.iv = custom_xkey.iv
        if custom_xkey.key != b'':
            self.key = custom_xkey.key
            return True
        if self.uri.startswith('http://') or self.uri.startswith('https://'):
            logger.info(f'key uri => {self.uri}')
            if platform.system() == 'Windows':
                asyncio.set_event_loop_policy(
                    asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.get_event_loop()
            self.key = loop.run_until_complete(self.fetch(self.uri, args))
        elif self.uri.startswith('ftp://'):
            return False
        return True
