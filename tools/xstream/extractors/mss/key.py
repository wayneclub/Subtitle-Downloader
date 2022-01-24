from tools.xstream.models.key import StreamKey
from .childs.protectionheader import ProtectionHeader


class MSSKey(StreamKey):
    def __init__(self, ph: ProtectionHeader):
        super(MSSKey, self).__init__()
        self.systemid = ph.SystemID
        self.key = ph.innertext
