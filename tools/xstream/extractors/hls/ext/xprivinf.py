from .x import X


class XPrivinf(X):
    '''
    #EXT-X-PRIVINF YOUKU的自定义标签
    - FILESIZE=925655
    '''
    def __init__(self):
        super(XPrivinf, self).__init__('#EXT-X-PRIVINF')
        self.filesize = None # type: int
        self.drm_notencrypt = False # type: bool
        self.known_attrs = {
            'FILESIZE': int,
        }

    def set_attrs_from_line(self, line: str):
        if line.endswith('DRM_NOTENCRYPT'):
            self.drm_notencrypt = True
            line = line.replace('DRM_NOTENCRYPT', '')
        return super(XPrivinf, self).set_attrs_from_line(line)