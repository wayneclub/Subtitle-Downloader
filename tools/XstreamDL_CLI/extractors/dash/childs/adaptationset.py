from ..mpditem import MPDItem


class AdaptationSet(MPDItem):
    def __init__(self, name: str):
        super(AdaptationSet, self).__init__(name)
        self.id = None
        self.contentType = None # type: str
        self.lang = None
        self.segmentAlignment = None
        self.maxWidth = None
        self.maxHeight = None
        self.frameRate = None
        self.par = None
        self.width = None
        self.height = None
        self.mimeType = None
        self.codecs = None

    def get_contenttype(self):
        if self.contentType is not None:
            return self.contentType
        if self.mimeType is not None:
            return self.mimeType.split('/')[0].title()

    def get_resolution(self):
        return f"{self.width}x{self.height}p"

    def get_suffix(self):
        return '.' + self.mimeType.split('/')[0].split('-')[-1]