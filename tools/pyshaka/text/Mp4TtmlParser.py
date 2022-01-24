from typing import List

from tools.pyshaka.text.Cue import Cue
from tools.pyshaka.text.TtmlTextParser import TtmlTextParser
from tools.pyshaka.util.Mp4Parser import Mp4Parser, ParsedBox
from tools.pyshaka.util.exceptions import InvalidMp4TTML
from tools.pyshaka.util.TextParser import TimeContext


class Mp4TtmlParser:

    def __init__(self):
        self.parser_ = TtmlTextParser()

    def set_timescale(self, timescale: int):
        pass

    def parseInit(self, data: memoryview):
        '''
        这个函数不调用也没什么问题
        '''
        def stpp_callback(box: ParsedBox):
            nonlocal sawSTPP
            sawSTPP = True
            box.parser.stop()

        sawSTPP = False
        # 初始化解析器
        mp4parser = Mp4Parser()
        # 给要准备解析的box添加对应的解析函数 后面回调
        mp4parser = mp4parser.box('moov', Mp4Parser.children)
        mp4parser = mp4parser.box('trak', Mp4Parser.children)
        mp4parser = mp4parser.box('mdia', Mp4Parser.children)
        mp4parser = mp4parser.box('minf', Mp4Parser.children)
        mp4parser = mp4parser.box('stbl', Mp4Parser.children)
        mp4parser = mp4parser.fullBox('stsd', Mp4Parser.sampleDescription)
        mp4parser = mp4parser.box('stpp', stpp_callback)
        # 解析数据
        mp4parser = mp4parser.parse(data)

        if not sawSTPP:
            raise InvalidMp4TTML(f'is sawSTPP? {sawSTPP}')

    def parseMedia(self, data: memoryview, time: TimeContext, dont_raise: bool = True) -> List[Cue]:

        def mdat_callback(data: bytes):
            nonlocal payload
            nonlocal sawMDAT
            sawMDAT = True
            payload.extend(self.parser_.parseMedia(data, time))

        sawMDAT = False
        payload = []

        mp4parser = Mp4Parser()
        mp4parser = mp4parser.box('mdat', Mp4Parser.allData(mdat_callback))
        mp4parser = mp4parser.parse(data, partialOkay=False)

        if not sawMDAT:
            if dont_raise:
                return payload
            else:
                raise InvalidMp4TTML(f'is sawMDAT? {sawMDAT}')
        return payload
