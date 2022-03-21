from ..mpditem import MPDItem


class Period(MPDItem):
    def __init__(self, name: str):
        super(Period, self).__init__(name)
        self.id = None # type: str
        self.start = None # type: float
        self.duration = None # type: float

    def generate(self):
        if isinstance(self.start, str):
            self.start = self.match_duration(self.start)
        # else:
        #     self.start = 0.0
        if isinstance(self.duration, str):
            self.duration = self.match_duration(self.duration)
        # else:
        #     self.duration = 0.0