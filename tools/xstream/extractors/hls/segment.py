import re
from tools.xstream.models.segment import Segment
from tools.xstream.extractors.hls.ext.xkey import XKey
from tools.xstream.extractors.hls.ext.xprivinf import XPrivinf


class HLSSegment(Segment):
    def __init__(self):
        super(HLSSegment, self).__init__()
        # 加密信息
        self.xkey = None  # type: XKey
        self.__xprivinf = None  # type: XPrivinf
        self.has_set_key = False

    def is_encrypt(self):
        if self.__xprivinf is not None:
            return self.__xprivinf.drm_notencrypt
        elif self.xkey is not None:
            return True
        else:
            return False

    def is_supported_encryption(self):
        if self.xkey is not None and self.xkey.method.upper() in ['AES-128']:
            return True
        return False

    def set_duration(self, line: str):
        try:
            self.duration = float(line.split(
                ':', maxsplit=1)[-1].split(',')[0])
        except Exception:
            pass

    def set_byterange(self, line: str):
        try:
            _ = line.split(':', maxsplit=1)[-1].split('@')
            total, offset = int(_[0]), int(_[1])
            self.byterange = [total, offset]
        except Exception:
            pass

    def set_privinf(self, line: str):
        '''
        对于分段来说 标签的属性值 应该归属在标签下面 计算时需要注意
        不过也可以在解析标签信息之后 进行赋值处理 这样便于调用
        '''
        self.__xprivinf = XPrivinf().set_attrs_from_line(line)
        if self.__xprivinf.filesize is not None:
            self.filesize = self.__xprivinf.filesize

    def set_url(self, home_url: str, base_url: str, line: str):
        if line.startswith('http://') or line.startswith('https://') or line.startswith('ftp://'):
            self.url = line
        elif line.startswith('/'):
            self.url = f'{home_url}/{line}'
        else:
            self.url = f'{base_url}/{line}'

    def set_map_url(self, home_url: str, base_url: str, line: str):
        map_uri = re.match('#EXT-X-MAP:URI="(.*?)"', line.strip())
        if map_uri is None:
            print('find #EXT-X-MAP tag, however has no uri')
            return
        map_uri = map_uri.group(1)
        if map_uri.startswith('http://') or map_uri.startswith('https://') or map_uri.startswith('ftp://'):
            self.url = map_uri
        elif map_uri.startswith('/'):
            self.url = f'{home_url}{map_uri}'
        else:
            self.url = f'{base_url}/{map_uri}'
        self.segment_type = 'map'
        # 每一条流理应只有一个map
        self.name = 'map.mp4'
        self.index = -1

    def set_key(self, home_url: str, base_url: str, line: str):
        self.has_set_key = True
        xkey = XKey().set_attrs_from_line(home_url, base_url, line)
        if xkey is not None:
            self.xkey = xkey

    def get_xkey(self):
        return self.xkey

    def set_xkey(self, last_segment_has_xkey: bool, xkey: XKey):
        '''
        如果已经因为#EXT-X-KEY而设置过xkey了
        那就不使用之前分段的xkey了
        '''
        if last_segment_has_xkey is False:
            return
        if self.has_set_key is True:
            return
        if xkey is None:
            return
        self.xkey = xkey
