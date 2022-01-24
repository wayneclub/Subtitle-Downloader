from ..mpditem import MPDItem


class Representation(MPDItem):
    def __init__(self, name: str):
        super(Representation, self).__init__(name)
        self.id = None
        self.scanType = None
        self.frameRate = None
        self.bandwidth = None
        self.codecs = None
        self.mimeType = None
        self.sar = None
        self.width = None
        self.height = None
        self.audioSamplingRate = None

    def get_contenttype(self):
        if self.mimeType is not None:
            return self.mimeType.split('/')[0].title()

    def get_resolution(self):
        return f"{self.width}x{self.height}p"

    def get_suffix(self):
        return '.' + self.mimeType.split('/')[0].split('-')[-1]