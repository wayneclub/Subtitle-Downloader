import re
from .x import X


class XMedia(X):
    '''
    #EXT-X-MEDIA 外挂媒体
    - TYPE=AUDIO,URI="",GROUP-ID="default-audio-group",NAME="stream_0",AUTOSELECT=YES,CHANNELS="2"
    '''
    def __init__(self):
        super(XMedia, self).__init__('#EXT-X-MEDIA')
        self.type = None # type: str
        self.uri = None # type: str
        self.group_id = None # type: str
        self.language = None # type: str
        self.assoc_language = None # type: str
        self.name = None # type: str
        self.default = None # type: str
        self.autoselect = None # type: str
        self.forced = None # type: str
        self.instream_id = None # type: str
        self.subtitles = None # type: str
        self.channels = None # type: int
        self.known_attrs = {
            'TYPE': 'type',
            'URI': 'uri',
            'GROUP-ID': 'group_id',
            'LANGUAGE': 'language',
            'ASSOC-LANGUAGE': 'assoc_language',
            'NAME': 'name',
            'DEFAULT': 'default',
            'AUTOSELECT': 'autoselect',
            'FORCED': 'forced',
            'INSTREAM-ID': 'instream_id',
            'CHARACTERISTICS': 'subtitles',
            'CHANNELS': int,
        }

    def convert_type(self, name: str, value: str, _type: type):
        if name == 'CHANNELS':
            try:
                value = re.findall('(\d+)', value)[0]
            except Exception:
                pass
        self.__setattr__(self.format_key(name), _type(value))

    def set_attrs_from_line(self, line: str):
        '''
        这里实际上可以不写
        '''
        return super(XMedia, self).set_attrs_from_line(line)