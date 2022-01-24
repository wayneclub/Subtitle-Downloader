from typing import Dict, Callable
from enum import Enum

# from tools.pyshaka.log import log
from tools.pyshaka.util.DataViewReader import DataViewReader, Endianness


class ParsedBox:
    '''
    js原本是在shaka.extern.ParsedBox中
    但是python中做分离会引起循环导入的问题
    加上ParsedBox定义是在externs/shaka/mp4_parser.js
    于是这里就把ParsedBox放到这里了
    '''

    def __init__(self, **kwargs):
        self.parser = kwargs['parser']  # type: Mp4Parser
        self.partialOkay = kwargs['partialOkay']  # type: bool
        self.start = kwargs['start']  # type: int
        self.size = kwargs['size']  # type: int
        self.version = kwargs['version']  # type: int
        self.flags = kwargs['flags']  # type: int
        self.reader = kwargs['reader']  # type: DataViewReader
        self.has64BitSize = kwargs['has64BitSize']  # type: bool


class Mp4Parser:

    class BoxType_(Enum):
        BASIC_BOX = 0
        FULL_BOX = 1

    def __init__(self):
        self.headers_ = {}  # type: Dict[int, Mp4Parser.BoxType_]
        self.boxDefinitions_ = {}  # type: Dict[int, Callable]
        self.done_ = False  # type: bool

    def box(self, _type: str, definition: Callable) -> 'Mp4Parser':
        typeCode = Mp4Parser.typeFromString_(_type)
        self.headers_[typeCode] = Mp4Parser.BoxType_.BASIC_BOX
        self.boxDefinitions_[typeCode] = definition
        return self

    def fullBox(self, _type: str, definition: Callable) -> 'Mp4Parser':
        typeCode = Mp4Parser.typeFromString_(_type)
        self.headers_[typeCode] = Mp4Parser.BoxType_.FULL_BOX
        self.boxDefinitions_[typeCode] = definition
        return self

    def stop(self):
        self.done_ = True

    def parse(self, data, partialOkay: bool = False, stopOnPartial: bool = False):
        reader = DataViewReader(data, Endianness.BIG_ENDIAN)
        self.done_ = False
        while reader.hasMoreData() and not self.done_:
            self.parseNext(0, reader, partialOkay, stopOnPartial)

    def parseNext(self, absStart: int, reader: DataViewReader, partialOkay: bool, stopOnPartial: bool = False):
        start = reader.getPosition()

        # size(4 bytes) + type(4 bytes) = 8 bytes
        if stopOnPartial and start + 8 > reader.getLength():
            self.done_ = True
            return

        size = reader.readUint32()
        _type = reader.readUint32()
        name = Mp4Parser.typeToString(_type)
        has64BitSize = False
        # log.info(f'[{name}] Parsing MP4 box')

        if size == 0:
            size = reader.getLength() - start
        elif size == 1:
            if stopOnPartial and reader.getPosition() + 8 > reader.getLength():
                self.done_ = True
                return
            size = reader.readUint64()
            has64BitSize = True
        # 和js不一样 py中不存在key会直接异常 所以这里用get方法
        boxDefinition = self.boxDefinitions_.get(_type)

        if boxDefinition:
            version = None
            flags = None

            if self.headers_[_type] == Mp4Parser.BoxType_.FULL_BOX:
                if stopOnPartial and reader.getPosition() + 4 > reader.getLength():
                    self.done_ = True
                    return
                versionAndFlags = reader.readUint32()
                version = versionAndFlags >> 24
                flags = versionAndFlags & 0xFFFFFF

            end = start + size
            if partialOkay and end > reader.getLength():
                end = reader.getLength()

            if stopOnPartial and end > reader.getLength():
                self.done_ = True
                return
            payloadSize = end - reader.getPosition()
            payload = reader.readBytes(payloadSize) if payloadSize > 0 else b''

            payloadReader = DataViewReader(payload, Endianness.BIG_ENDIAN)

            box = {
                'parser': self,
                'partialOkay': partialOkay or False,
                'version': version,
                'flags': flags,
                'reader': payloadReader,
                'size': size,
                'start': start + absStart,
                'has64BitSize': has64BitSize,
            }
            box = ParsedBox(**box)

            boxDefinition(box)
        else:
            skipLength = min(start + size - reader.getPosition(),
                             reader.getLength() - reader.getPosition())
            reader.skip(skipLength)

    @staticmethod
    def children(box: ParsedBox):
        headerSize = Mp4Parser.headerSize(box)
        while box.reader.hasMoreData() and not box.parser.done_:
            box.parser.parseNext(box.start + headerSize,
                                 box.reader, box.partialOkay)

    @staticmethod
    def sampleDescription(box: ParsedBox):
        headerSize = Mp4Parser.headerSize(box)
        count = box.reader.readUint32()
        for _ in range(count):
            box.parser.parseNext(box.start + headerSize,
                                 box.reader, box.partialOkay)
            if box.parser.done_:
                break

    @staticmethod
    def allData(callback: Callable):
        def alldata_callback(box: ParsedBox):
            _all = box.reader.getLength() - box.reader.getPosition()
            return callback(box.reader.readBytes(_all))
        return alldata_callback

    @staticmethod
    def typeFromString_(name: str):
        assert len(name) == 4, 'Mp4 box names must be 4 characters long'

        code = 0
        for char in name:
            code = (code << 8) | ord(char)
        return code

    @staticmethod
    def typeToString(_type: int):
        name = bytes([
            (_type >> 24) & 0xff,
            (_type >> 16) & 0xff,
            (_type >> 8) & 0xff,
            _type & 0xff
        ]).decode('utf-8')
        return name

    @staticmethod
    def headerSize(box: ParsedBox):
        return 8 + (8 if box.has64BitSize else 0) + (4 if box.flags is not None else 0)
