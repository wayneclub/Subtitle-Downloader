import re
from urllib.parse import urlparse
from tools.XstreamDL_CLI.models.segment import Segment


class DASHSegment(Segment):
    def __init__(self):
        super(DASHSegment, self).__init__()
        self.suffix = '.mp4'

    def is_encrypt(self):
        return True

    def is_supported_encryption(self):
        return False

    def set_duration(self, duration: float):
        self.duration = duration

    def set_fmt_time(self, fmt_time: float):
        self.fmt_time = fmt_time

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

    def get_url_name(self, url: str):
        url_name = urlparse(url).path.split('/')[-1]
        match = re.match('Fragments\((.+?)\)', url_name)
        if match:
            url_name = match.group(1).split(
                ',')[0].replace('=', '_') + self.suffix
        return url_name

    def set_media_url(self, media_url: str, name_from_url: bool = False):
        parts = media_url.split('?')[0].split('/')[-1].split('.')
        if len(parts) > 1:
            # 修正后缀
            self.suffix = f'.{parts[-1]}'
            self.name = f'{self.index:0>4}.{parts[-1]}'
        self.url = media_url
        if name_from_url:
            self.name = self.get_url_name(self.url)
