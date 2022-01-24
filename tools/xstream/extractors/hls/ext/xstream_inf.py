from .x import X


class XStreamInf(X):
    '''
    #EXT-X-STREAM-INF 紧接着该标签的实际上是一个Stream
    - PROGRAM-ID=1,BANDWIDTH=1470188,SIZE=468254984,FPS=25,RESOLU=1080,CODECS="avc1,mp4a",QUALITY=5,STREAMTYPE="mp4hd3"
    #EXT-X-I-FRAME-STREAM-INF 也被归类于此 有一个额外属性 URI
    '''
    def __init__(self):
        super(XStreamInf, self).__init__('#EXT-X-STREAM-INF')
        self.program_id = None # type: int
        self.bandwidth = None # type: int
        self.average_bandwidth = None # type: int
        self.codecs = None # type: str
        self.resolution = '' # type: str
        self.frame_rate = None # type: float
        self.hdcp_level = None # type: str
        self.characteristics = None # type: str
        self.uri = None # type: str
        self.audio = None # type: str
        self.video = None # type: str
        self.subtitles = None # type: str
        self.closed_captions = None # type: str
        self.video_range = None # type: str
        self.size = None # type: int
        self.fps = None # type: float
        self.quality = None # type: int
        self.streamtype = '' # type: str
        # VIDEO-RANGE是苹果的标准 往下的是非标准属性
        self.known_attrs = {
            'PROGRAM-ID': int,
            'BANDWIDTH': int,
            'AVERAGE-BANDWIDTH': int,
            'CODECS': 'codecs',
            'RESOLUTION': 'resolution',
            'FRAME-RATE': float,
            'HDCP-LEVEL': 'hdcp_level',
            'CHARACTERISTICS': 'characteristics',
            'URI': 'uri',
            'AUDIO': 'audio',
            'VIDEO': 'video',
            'SUBTITLES': 'subtitles',
            'CLOSED-CAPTIONS': 'closed_captions',
            'VIDEO-RANGE': 'video_range',
            'SIZE': int,
            'FPS': float,
            'RESOLU': 'resolution',
            'QUALITY': int,
            'STREAMTYPE': 'streamtype',
        }

    def set_attrs_from_line(self, line: str):
        '''
        这里实际上可以不写
        '''
        return super(XStreamInf, self).set_attrs_from_line(line)