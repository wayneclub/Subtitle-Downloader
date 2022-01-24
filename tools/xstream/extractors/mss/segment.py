from tools.xstream.models.segment import Segment


class MSSSegment(Segment):
    def __init__(self):
        super(MSSSegment, self).__init__()
        self.suffix = '.mp4'
        self.has_protection = False

    def set_protection_flag(self, flag: bool):
        self.has_protection = flag

    def is_encrypt(self):
        return self.has_protection

    def is_supported_encryption(self):
        return False

    def is_ism(self):
        return True

    def set_duration(self, duration: float):
        self.duration = duration

    def set_subtitle_url(self, subtitle_url: str):
        self.name = subtitle_url.split('?')[0].split('/')[-1]
        self.index = -1
        self.url = subtitle_url
        self.segment_type = 'init'

    def set_init_url(self, init_url: str):
        parts = init_url.split('?')[0].split('/')[-1].split('.')
        if len(parts) > 1:
            self.suffix = f'.{parts[-1]}'
        self.name = f'init{self.suffix}'
        self.index = -1
        self.url = init_url
        self.segment_type = 'init'

    def set_media_url(self, media_url: str):
        parts = media_url.split('?')[0].split('/')[-1].split('.')
        if len(parts) > 1:
            # 修正后缀
            self.suffix = f'.{parts[-1]}'
            self.name = f'{self.index:0>4}.{parts[-1]}'
        self.url = media_url
