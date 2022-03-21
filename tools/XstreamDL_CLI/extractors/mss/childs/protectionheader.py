import re
import base64
from ..ismitem import ISMItem


class ProtectionHeader(ISMItem):
    def __init__(self, name: str):
        super(ProtectionHeader, self).__init__(name)
        self.SystemID = None # type: str
        self.kid = bytes([0] * 16) # type: bytes

    def generate(self):
        '''
        get kid from innertext
        '''
        # dAIAAAEAAQBqAjwAVwBSAE0ASABFAEEARABFAFIAIAB4AG0AbABuAHMAPQAiAGgAdAB0AHAAOgAvAC8AcwBjAGgAZQBtAGEAcwAuAG0AaQBjAHIAbwBzAG8AZgB0AC4AYwBvAG0ALwBEAFIATQAvADIAMAAwADcALwAwADMALwBQAGwAYQB5AFIAZQBhAGQAeQBIAGUAYQBkAGUAcgAiACAAdgBlAHIAcwBpAG8AbgA9ACIANAAuADAALgAwAC4AMAAiAD4APABEAEEAVABBAD4APABQAFIATwBUAEUAQwBUAEkATgBGAE8APgA8AEsARQBZAEwARQBOAD4AMQA2ADwALwBLAEUAWQBMAEUATgA+ADwAQQBMAEcASQBEAD4AQQBFAFMAQwBUAFIAPAAvAEEATABHAEkARAA+ADwALwBQAFIATwBUAEUAQwBUAEkATgBGAE8APgA8AEsASQBEAD4ATwBXAGoAaAB0AHIAMwB1ADkAawArAHIAZABvADEASQBMAFkAMAByAGEAZwA9AD0APAAvAEsASQBEAD4APABDAEgARQBDAEsAUwBVAE0APgBOADgAVABvAEsASABKADEAZABKAGMAPQA8AC8AQwBIAEUAQwBLAFMAVQBNAD4APABMAEEAXwBVAFIATAA+AGgAdAB0AHAAcwA6AC8ALwBhAHAAaQAuAGIAbABpAG0ALgBjAG8AbQAvAGwAaQBjAGUAbgBzAGUALwBwAGwAYQB5AHIAZQBhAGQAeQA8AC8ATABBAF8AVQBSAEwAPgA8AC8ARABBAFQAQQA+ADwALwBXAFIATQBIAEUAQQBEAEUAUgA+AA==
        try:
            data = base64.b64decode(self.innertext).replace(b'\x00', b'')
            b64_kid = re.findall(b'<KID>(.+?)</KID>', data)[0].decode('utf-8')
            _kid = base64.b64decode(b64_kid)
            self.kid = bytes([_kid[3], _kid[2], _kid[1], _kid[0], _kid[5], _kid[4], _kid[7], _kid[6], *list(_kid[8:])])
        except Exception as e:
            print(f'ProtectionHeader generate failed, reason:{e}')