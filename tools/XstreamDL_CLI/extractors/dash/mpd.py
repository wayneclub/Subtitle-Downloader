from datetime import datetime
from .mpditem import MPDItem


class MPD(MPDItem):
    def __init__(self, name: str):
        super(MPD, self).__init__(name)
        self.maxSegmentDuration = None # type: str
        self.mediaPresentationDuration = None # type: str
        self.minBufferTime = None # type: str
        # live profile
        # - urn:mpeg:dash:profile:isoff-live:2011
        # - urn:mpeg:dash:profile:isoff-ext-live:2014
        self.profiles = None # type: str
        # dynamic -> live
        # static -> live playback
        self.type = None # type: str
        # only use when type is 'dynamic' which specifies the smallest period between potential changes to the MPD
        self.minimumUpdatePeriod = None # type: str
        # time of client to fetch the mpd content
        self.publishTime = None # type: datetime
        self.availabilityStartTime = None # type: float
        self.timeShiftBufferDepth = None # type: str
        self.suggestedPresentationDelay = None # type: str

    def generate(self):
        if isinstance(self.maxSegmentDuration, str):
            self.maxSegmentDuration = self.match_duration(self.maxSegmentDuration)
        if isinstance(self.mediaPresentationDuration, str):
            self.mediaPresentationDuration = self.match_duration(self.mediaPresentationDuration)
        if isinstance(self.minBufferTime, str):
            self.minBufferTime = self.match_duration(self.minBufferTime)
        if isinstance(self.availabilityStartTime, str):
            if self.availabilityStartTime in ['1970-01-01T00:00:00Z', '1970-01-01T00:00:00.000Z']:
                self.availabilityStartTime = 0.0
            # 2019-03-05T08:26:06.748000+00:00
            if isinstance(self.availabilityStartTime, str) and self.availabilityStartTime[-9:] == '000+00:00':
                self.availabilityStartTime = self.availabilityStartTime[:-9] + 'Z'
            try:
                self.availabilityStartTime = datetime.strptime(self.availabilityStartTime, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
            except Exception:
                try:
                    self.availabilityStartTime = datetime.strptime(self.availabilityStartTime, '%Y-%m-%dT%H:%M:%SZ').timestamp()
                except Exception:
                    pass
        if isinstance(self.publishTime, str):
            is_match = False
            try:
                self.publishTime = datetime.strptime(self.publishTime, '%Y-%m-%dT%H:%M:%S.%fZ')
                is_match = True
            except Exception:
                pass
            if is_match is False:
                try:
                    self.publishTime = datetime.strptime(self.publishTime, '%Y-%m-%dT%H:%M:%SZ')
                    is_match = True
                except Exception:
                    pass
            if is_match is False:
                try:
                    # 2021-11-28T12:33:53
                    self.publishTime = datetime.strptime(self.publishTime, '%Y-%m-%dT%H:%M:%S')
                    is_match = True
                except Exception:
                    pass
            if is_match is False:
                try:
                    # 2022-02-14T11:43:04+00:00
                    self.publishTime = datetime.strptime(self.publishTime.split('+')[0], '%Y-%m-%dT%H:%M:%S')
                    is_match = True
                except Exception:
                    pass
            if is_match is False:
                assert is_match is True, f'match publishTime failed => {self.publishTime}'