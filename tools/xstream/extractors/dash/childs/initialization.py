from ..mpditem import MPDItem


class Initialization(MPDItem):

    def __init__(self, name: str):
        super(Initialization, self).__init__(name)
        self.sourceURL = ""