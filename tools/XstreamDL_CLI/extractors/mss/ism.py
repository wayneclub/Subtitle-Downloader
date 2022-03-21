from .ismitem import ISMItem


class ISM(ISMItem):
    def __init__(self, name: str):
        super(ISM, self).__init__(name)
        self.MajorVersion = None # type: str
        self.MinorVersion = None # type: str
        self.TimeScale = None # type: int
        self.Duration = None # type: int

    def generate(self):
        self.to_int('TimeScale')
        self.to_int('Duration')