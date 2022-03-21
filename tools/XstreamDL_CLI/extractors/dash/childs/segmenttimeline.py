from ..mpditem import MPDItem


class SegmentTimeline(MPDItem):
    # 5.3.9.6 Segment timeline
    def __init__(self, name: str):
        super(SegmentTimeline, self).__init__(name)