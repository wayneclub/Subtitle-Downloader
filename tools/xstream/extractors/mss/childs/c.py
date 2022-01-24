from ..ismitem import ISMItem


class c(ISMItem):
    def __init__(self, name: str):
        super(c, self).__init__(name)
        self.t = None # type: int
        self.d = None # type: int
        self.r = 1 # type: int

    def generate(self):
        if self.t is not None:
            self.to_int('t')
        self.to_int('d')
        self.to_int('r')