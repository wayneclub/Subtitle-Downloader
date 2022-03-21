from ..mpditem import MPDItem


class CencPssh(MPDItem):
    def __init__(self, name: str):
        super(CencPssh, self).__init__(name)