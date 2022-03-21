from typing import List
from pathlib import Path


class Segment:
    '''
    每一个分段应当具有以下基本属性：
    - 名称
    - 索引
    - 后缀
    - 链接
    - 文件大小
    - 时长
    - 二进制内容
    - 下载文件夹
    - 分段类型
    '''
    def __init__(self):
        self.name = ''
        self.index = 0
        self.suffix = '.ts'
        self.url = ''
        self.filesize = 0
        self.duration = 0.0
        # dash直播流需要通过比较时间来确定是不是需要下载
        self.fmt_time = 0
        self.byterange = [] # type: list
        # <---临时存放二进制内容--->
        self.content = [] # type: List[bytes]
        # <---分段临时下载文件夹--->
        self.folder = None # type: Path
        # <---分段类型--->
        self.segment_type = 'normal'
        self.skip_concat = False
        # 直播流 单个分段 最大404次数
        self.max_retry_404 = 5

    def is_ism(self) -> bool:
        ''' 请重写 '''
        return False

    def is_encrypt(self) -> bool:
        ''' 请重写 '''
        pass

    def is_supported_encryption(self) -> bool:
        ''' 请重写 '''
        pass

    def add_offset_for_name(self, offset: int, has_init: bool = False, name_from_url: bool = False):
        self.index += offset
        if has_init:
            self.index -= 1
        if name_from_url is False:
            self.name = f'{self.index:0>4}{self.suffix}'

    def set_offset_for_name(self, offset: int, has_init: bool = False, name_from_url: bool = False):
        self.index = offset
        if has_init:
            self.index -= 1
        if name_from_url is False:
            self.name = f'{self.index:0>4}{self.suffix}'

    def set_index(self, index: str):
        self.index = index
        if index == -1:
            self.name = f'init{self.suffix}'
        else:
            self.name = f'{self.index:0>4}{self.suffix}'
        return self

    def set_folder(self, folder: Path):
        self.folder = folder
        return self

    def get_path(self) -> Path:
        return self.folder / self.name

    def dump(self) -> bool:
        self.get_path().write_bytes(b''.join(self.content))
        self.content = []
        return True