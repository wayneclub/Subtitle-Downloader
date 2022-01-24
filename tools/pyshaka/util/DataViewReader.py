import struct
from enum import Enum

from tools.pyshaka.util.exceptions import OutOfBoundsError
from tools.pyshaka.util.exceptions import IntOverflowError


class Endianness(Enum):
    BIG_ENDIAN = 0
    LITTLE_ENDIAN = 1


class DataView:
    '''
    shaka/util/buffer_utils.js
    '''

    def __init__(self, data: bytes):
        self.buffer = memoryview(bytearray(data))
        # self.buffer = memoryview(bytearray([0x96, 0x87, 0xac]))
        self.byteLength = len(self.buffer)  # type: int

    def getUint8(self):
        pass

    def getUint16(self):
        pass

    def getUint32(self, position: int, littleEndian: bool = False):
        # 这里记得切片长度要补齐4位 不然unpack会报错
        buf = self.buffer[position:position + 4].tobytes()
        if len(buf) < 4:
            buf = b'\x00' * (4 - len(buf)) + buf
        if littleEndian:
            return struct.unpack("<I", buf)[0]
        else:
            return struct.unpack(">I", buf)[0]

    def getUint64(self, position: int, littleEndian: bool = False):
        # 这里记得切片长度要补齐4位 不然
        buf = self.buffer[position:position + 4].tobytes()
        if len(buf) < 4:
            buf = b'\x00' * (4 - len(buf)) + buf
        if littleEndian:
            return struct.unpack("<I", buf)[0]
        else:
            return struct.unpack(">I", buf)[0]

    def getInt8(self):
        pass

    def getInt16(self):
        pass

    def getInt32(self, position: int, littleEndian: bool = False):
        buf = self.buffer[position:position + 4].tobytes()
        if len(buf) < 4:
            buf = b'\x00' * (4 - len(buf)) + buf
        if littleEndian:
            return struct.unpack("<i", buf)[0]
        else:
            return struct.unpack(">i", buf)[0]

    def getInt64(self):
        pass

    def readUint8(self):
        pass

    def readUint16(self):
        pass

    def readUint32(self):
        pass

    def readInt8(self):
        pass

    def readInt16(self):
        pass

    def readInt32(self):
        pass

    def readInt64(self):
        pass

    @staticmethod
    def toUint8(data: 'DataView', offset: int = 0, length: int = None):
        # 由于python中float('inf')表示无穷大 但不能作为索引
        # 所以这里直接将最大长度视为byteLength
        if length is None:
            length = data.byteLength
        return data.buffer[offset:offset + length].tobytes()


class DataViewReader(DataView):
    '''
    shaka/util/data_view_reader.js
    '''

    def __init__(self, data: bytes, endianness: Endianness):
        self.dataView_ = DataView(data)  # type: DataView
        self.littleEndian_ = endianness == Endianness.LITTLE_ENDIAN  # type: bool
        self.position_ = 0  # type: int

    def getDataView(self) -> DataView:
        return self.dataView_

    def hasMoreData(self) -> bool:
        return self.position_ < self.dataView_.byteLength

    def getPosition(self) -> int:
        return self.position_

    def getLength(self) -> int:
        return self.dataView_.byteLength

    def readUint8(self):
        pass

    def readUint16(self):
        pass

    def readUint32(self) -> int:
        value = self.dataView_.getUint32(self.position_, self.littleEndian_)
        self.position_ += 4
        return value

    def readInt32(self):
        value = self.dataView_.getInt32(self.position_, self.littleEndian_)
        self.position_ += 4
        return value

    def readUint64(self) -> int:
        if self.littleEndian_:
            low = self.dataView_.getUint32(self.position_, True)
            high = self.dataView_.getUint32(self.position_ + 4, True)
        else:
            high = self.dataView_.getUint32(self.position_, False)
            low = self.dataView_.getUint32(self.position_ + 4, False)

        if high > 0x1FFFFF:
            raise IntOverflowError

        self.position_ += 8
        return (high * (2 ** 32)) + low

    def readBytes(self, length: int):
        assert length >= 0, 'Bad call to DataViewReader.readBytes'
        if self.position_ + length > self.dataView_.byteLength:
            raise OutOfBoundsError
        data = DataView.toUint8(self.dataView_, self.position_, length)
        self.position_ += length
        return data

    def skip(self, length: int):
        assert length >= 0, 'Bad call to DataViewReader.skip'
        if self.position_ + length > self.dataView_.byteLength:
            raise OutOfBoundsError
        self.position_ += length

    def rewind(self, length: int):
        pass

    def seek(self, position: int):
        pass

    def readTerminatedString(self):
        pass

    def outOfBounds_(self):
        pass
