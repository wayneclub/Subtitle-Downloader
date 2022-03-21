from ..mpditem import MPDItem


class SegmentBaee(MPDItem):

    def __init__(self, name: str):
        super(SegmentBaee, self).__init__(name)
        self.indexRange = ""
        self.timescale = None # type: int
        self.presentationTimeOffset = None # type: int

    def generate(self):
        if self.presentationTimeOffset is None:
            self.presentationTimeOffset = 0
        if self.timescale is None:
            self.timescale = 0
        self.to_int()

    def to_int(self):
        self.timescale = int(self.timescale)
        self.presentationTimeOffset = int(self.presentationTimeOffset)