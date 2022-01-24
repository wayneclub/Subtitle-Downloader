from ..ismitem import ISMItem


class StreamIndex(ISMItem):
    def __init__(self, name: str):
        super(StreamIndex, self).__init__(name)
        # <----- 通用 ----->
        self.Type = None # type: str
        self.QualityLevels = None # type: int
        self.TimeScale = None # type: int
        self.Name = None # type: str
        self.Chunks = None # type: int
        self.Url = None # type: str
        # <----- 视频 ----->
        self.MaxWidth = None # type: str
        self.MaxHeight = None # type: str
        self.DisplayWidth = None # type: str
        self.DisplayHeight = None # type: str
        # <----- 字幕 & 音频 ----->
        self.Language = None # type: str
        # <----- 字幕 ----->
        self.Subtype = None # type: str
        self.Language = None # type: str

    def generate(self):
        self.to_int('QualityLevels')
        self.to_int('Chunks')
        self.to_int('TimeScale')

    def get_media_url(self) -> str:
        return self.Url