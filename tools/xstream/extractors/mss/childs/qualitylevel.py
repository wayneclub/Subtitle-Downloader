from ..ismitem import ISMItem


class QualityLevel(ISMItem):
    '''
    https://docs.microsoft.com/en-us/iis/extensions/smooth-streaming-client/qualitylevel-attributes-iis-smooth-streaming
    '''
    def __init__(self, name: str):
        super(QualityLevel, self).__init__(name)
        # <----- 通用 ----->
        self.Index = None # type: int
        self.Bitrate = None # type: int
        self.CodecPrivateData = None # type: str
        self.FourCC = None # type: str
        self.NALUnitLengthField = None # type: int
        # <----- 音频 ----->
        self.SamplingRate = None # type: int
        self.Channels = None # type: int
        self.BitsPerSample = None # type: int
        self.PacketSize = None # type: int
        self.AudioTag = None # type: str
        # <----- 视频 ----->
        self.MaxWidth = None # type: str
        self.MaxHeight = None # type: str

    def generate(self):
        self.to_int('Index')
        self.to_int('Bitrate')
        self.to_int('SamplingRate')
        self.to_int('Channels')
        self.to_int('BitsPerSample')
        self.to_int('PacketSize')