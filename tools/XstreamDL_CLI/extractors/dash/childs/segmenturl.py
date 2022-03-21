from ..mpditem import MPDItem


class SegmentURL(MPDItem):

    def __init__(self, name: str):
        super(SegmentURL, self).__init__(name)
        self.media = ""