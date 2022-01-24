from ..mpditem import MPDItem


class SegmentList(MPDItem):

    def __init__(self, name: str):
        super(SegmentList, self).__init__(name)
        self.timescale = 0 # type: int
        self.duration = 0 # type: int

    def generate(self):
        self.to_int()

    def to_int(self):
        try:
            self.timescale = int(self.timescale)
            self.duration = int(self.duration)
        except Exception:
            pass