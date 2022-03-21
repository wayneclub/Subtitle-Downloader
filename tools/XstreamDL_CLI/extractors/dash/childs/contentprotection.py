from ..mpditem import MPDItem


class ContentProtection(MPDItem):
    def __init__(self, name: str):
        super(ContentProtection, self).__init__(name)
        self.value = None
        self.schemeIdUri = None
        self.cenc_default_KID = None