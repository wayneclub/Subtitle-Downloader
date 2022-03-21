from ..mpditem import MPDItem


class BaseURL(MPDItem):
    def __init__(self, name: str):
        super(BaseURL, self).__init__(name)
        self.serviceLocation = None # type: str
        self.dvb_priority = None # type: str
        self.dvb_weight = None # type: str