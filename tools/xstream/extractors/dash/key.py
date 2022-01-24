from typing import List
from tools.xstream.models.key import StreamKey
from .childs.contentprotection import ContentProtection
from .childs.cencpssh import CencPssh


class COMMON_MPEG:
    def __init__(self, schemeiduri: str, cenc_default_kid: str, value: str):
        self.schemeiduri = schemeiduri
        self.cenc_default_kid = cenc_default_kid
        self.value = value


class COMMON_CENC:
    def __init__(self, schemeiduri: str, cenc_pssh: str, value: str):
        self.schemeiduri = schemeiduri
        self.cenc_pssh = cenc_pssh
        self.value = value


class MARLIN:
    def __init__(self, schemeiduri: str, mas_marlincontentids: list):
        self.schemeiduri = schemeiduri
        self.mas_marlincontentids = mas_marlincontentids


class PLAYREADY:
    def __init__(self, schemeiduri: str, mspr_pro: str):
        self.schemeiduri = schemeiduri
        self.mspr_pro = mspr_pro


class WIDEVINE:
    def __init__(self, schemeiduri: str, cenc_pssh: str):
        self.schemeiduri = schemeiduri
        self.cenc_pssh = cenc_pssh


class PRIMETIME:
    def __init__(self, schemeiduri: str, cenc_pssh: str):
        self.schemeiduri = schemeiduri
        self.cenc_pssh = cenc_pssh


class DASHKey(StreamKey):
    def __init__(self, cp: ContentProtection):
        super(DASHKey, self).__init__()
        key = ''
        method = ''
        # https://dashif.org/identifiers/content_protection/
        if cp.schemeIdUri == 'urn:mpeg:dash:mp4protection:2011':
            key = COMMON_MPEG(cp.schemeIdUri, cp.cenc_default_KID, cp.value)
            method = 'COMMON_MPEG'
        elif cp.schemeIdUri == 'urn:uuid:1077efec-c0b2-4d02-ace3-3c1e52e2fb4b':
            key = COMMON_CENC(cp.schemeIdUri, self.get_pssh(cp), cp.value)
            method = 'COMMON_CENC'
        elif cp.schemeIdUri == 'urn:uuid:5E629AF5-38DA-4063-8977-97FFBD9902D4':
            key = MARLIN(cp.schemeIdUri, [])
            method = 'MARLIN'
        elif cp.schemeIdUri == 'urn:uuid:9a04f079-9840-4286-ab92-e65be0885f95':
            mspr_pros = cp.find('mspr:pros')  # type: List[CencPssh]
            if len(mspr_pros) > 0:
                mspr_pro = mspr_pros[0].innertext
            else:
                mspr_pro = ''
            key = PLAYREADY(cp.schemeIdUri, mspr_pro)
            method = 'PLAYREADY'
        elif cp.schemeIdUri == 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed':
            key = WIDEVINE(cp.schemeIdUri, self.get_pssh(cp))
            method = 'WIDEVINE'
        elif cp.schemeIdUri == 'urn:uuid:F239E769-EFA3-4850-9C16-A903C6932EFB':
            key = '???????'
            method = 'PRIMETIME'
        self.method = method
        self.key = key

    def get_pssh(self, cp: ContentProtection) -> str:
        cenc_psshs = cp.find('cenc:pssh')  # type: List[CencPssh]
        if len(cenc_psshs) > 0:
            return cenc_psshs[0].innertext
        else:
            return ''
