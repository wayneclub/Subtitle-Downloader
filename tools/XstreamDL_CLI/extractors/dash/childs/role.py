from ..mpditem import MPDItem


class Role(MPDItem):
    def __init__(self, name: str):
        super(Role, self).__init__(name)
        self.schemeIdUri = None
        self.value = None