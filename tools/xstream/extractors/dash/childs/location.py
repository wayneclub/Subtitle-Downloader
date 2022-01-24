from ..mpditem import MPDItem


class Location(MPDItem):
    def __init__(self, name: str):
        super(Location, self).__init__(name)