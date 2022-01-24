from ..mpditem import MPDItem


class S(MPDItem):
    '''
    5.3.9.6 Segment timeline
    - t -> presentationTimeOffset
    - d -> duration
    - r -> repeat
    '''
    def __init__(self, name: str):
        super(S, self).__init__(name)
        self.t = None # type: int
        self.d = None # type: int
        self.r = None # type: int

    def generate(self):
        if self.t is None:
            self.t = 0
        if self.d is None:
            self.d = 0
        if self.r is None:
            self.r = 0
        self.to_int()
        self.r += 1

    def to_int(self):
        self.t = int(self.t)
        self.d = int(self.d)
        self.r = int(self.r)