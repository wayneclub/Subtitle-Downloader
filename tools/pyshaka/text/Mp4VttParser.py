from typing import List
from tools.pyshaka.text.Cue import Cue
# from tools.pyshaka.text.TextEngine import TextEngine
from tools.pyshaka.text.VttTextParser import VttTextParser
from tools.pyshaka.util.DataViewReader import DataViewReader, Endianness
# from tools.pyshaka.util.Error import Error
# from tools.pyshaka.util.Functional import Functional
from tools.pyshaka.util.Mp4Parser import Mp4Parser, ParsedBox
from tools.pyshaka.util.Mp4BoxParsers import Mp4BoxParsers, ParsedTRUNSample
# from tools.pyshaka.util.StringUtils import StringUtils
# from tools.pyshaka.util.TextParser import TextParser
from tools.pyshaka.util.TextParser import TimeContext
from tools.pyshaka.util.exceptions import InvalidMp4VTT
from tools.pyshaka.log import log


class Mp4VttParser:

    def __init__(self):
        self.timescale_ = None  # type: int

    def set_timescale(self, timescale: int):
        self.timescale_ = timescale

    def parseInit(self, data: memoryview):
        # log.info('parseInit start')

        def mdhd_callback(box: ParsedBox):
            assert box.version == 0 or box.version == 1, 'MDHD version can only be 0 or 1'
            parsedMDHDBox = Mp4BoxParsers.parseMDHD(box.reader, box.version)
            self.timescale_ = parsedMDHDBox.timescale

        def wvtt_callback(box: ParsedBox):
            nonlocal sawWVTT
            sawWVTT = True

        sawWVTT = False
        # 初始化解析器
        mp4parser = Mp4Parser()
        # 给要准备解析的box添加对应的解析函数 后面回调
        mp4parser = mp4parser.box('moov', Mp4Parser.children)
        mp4parser = mp4parser.box('trak', Mp4Parser.children)
        mp4parser = mp4parser.box('mdia', Mp4Parser.children)
        mp4parser = mp4parser.fullBox('mdhd', mdhd_callback)
        mp4parser = mp4parser.box('minf', Mp4Parser.children)
        mp4parser = mp4parser.box('stbl', Mp4Parser.children)
        mp4parser = mp4parser.fullBox('stsd', Mp4Parser.sampleDescription)
        mp4parser = mp4parser.box('wvtt', wvtt_callback)
        # 解析数据
        mp4parser = mp4parser.parse(data)

        if not self.timescale_:
            raise InvalidMp4VTT(
                'Missing timescale for VTT content. It should be located in the MDHD.')

        if not sawWVTT:
            raise InvalidMp4VTT(
                'A WVTT box should have been seen (a valid vtt init segment with no actual subtitles')

    def parseMedia(self, data: memoryview, time: TimeContext) -> List[Cue]:

        def tfdt_callback(box: ParsedBox):
            nonlocal baseTime
            nonlocal sawTFDT
            sawTFDT = True
            assert box.version == 0 or box.version == 1, 'TFDT version can only be 0 or 1'
            parsedTFDTBox = Mp4BoxParsers.parseTFDT(box.reader, box.version)
            baseTime = parsedTFDTBox.baseMediaDecodeTime

        def tfhd_callback(box: ParsedBox):
            nonlocal defaultDuration
            assert box.flags is not None, 'A TFHD box should have a valid flags value'
            parsedTFHDBox = Mp4BoxParsers.parseTFHD(box.reader, box.flags)
            defaultDuration = parsedTFHDBox.defaultSampleDuration

        def trun_callback(box: ParsedBox):
            nonlocal sawTRUN
            nonlocal presentations
            sawTRUN = True
            assert box.version is not None, 'A TRUN box should have a valid version value'
            assert box.version is not None, 'A TRUN box should have a valid flags value'
            parsedTRUNBox = Mp4BoxParsers.parseTRUN(
                box.reader, box.version, box.flags)
            presentations = parsedTRUNBox.sampleData

        def mdat_callback(data: bytes):
            nonlocal sawMDAT
            nonlocal rawPayload
            assert not sawMDAT, 'VTT cues in mp4 with multiple MDAT are not currently supported'
            sawMDAT = True
            rawPayload = data

        if not self.timescale_:
            raise InvalidMp4VTT('No init segment for MP4+VTT!')

        baseTime = 0
        presentations = []  # type: List[ParsedTRUNSample]
        rawPayload = b''  # type: bytes
        cues = []  # type: List[Cue]

        sawTFDT = False
        sawTRUN = False
        sawMDAT = False
        defaultDuration = None

        mp4parser = Mp4Parser()
        mp4parser = mp4parser.box('moof', Mp4Parser.children)
        mp4parser = mp4parser.box('traf', Mp4Parser.children)
        mp4parser = mp4parser.fullBox('tfdt', tfdt_callback)
        mp4parser = mp4parser.fullBox('tfhd', tfhd_callback)
        mp4parser = mp4parser.fullBox('trun', trun_callback)
        mp4parser = mp4parser.box('mdat', Mp4Parser.allData(mdat_callback))
        mp4parser = mp4parser.parse(data, partialOkay=False)

        if not sawMDAT and not sawTFDT and not sawTRUN:
            raise InvalidMp4VTT(
                f'A required box is missing. Is saw: MDAT {sawMDAT} TFDT {sawTFDT} TRUN {sawTRUN}')

        currentTime = baseTime

        reader = DataViewReader(rawPayload, Endianness.BIG_ENDIAN)
        for presentation in presentations:
            duration = presentation.sampleDuration or defaultDuration
            if presentation.sampleCompositionTimeOffset:
                startTime = baseTime + presentation.sampleCompositionTimeOffset
            else:
                startTime = currentTime
            currentTime = startTime + (duration or 0)
            totalSize = 0
            while True:
                # Read the payload size.
                payloadSize = reader.readUint32()
                totalSize += payloadSize
                # Skip the type.
                payloadType = reader.readUint32()
                payloadName = Mp4Parser.typeToString(payloadType)

                # Read the data payload.
                payload = None
                if payloadName == 'vttc':
                    if payloadSize > 8:
                        payload = reader.readBytes(payloadSize - 8)
                elif payloadName == 'vtte':
                    # It's a vtte, which is a vtt cue that is empty. Ignore any data that does exist.
                    reader.skip(payloadSize - 8)
                else:
                    log.error(f'Unknown box {payloadName}! Skipping!')
                    reader.skip(payloadSize - 8)

                if duration:
                    if payload:
                        assert self.timescale_ is not None, 'Timescale should not be null!'
                        cue = Mp4VttParser.parseVTTC_(
                            payload,
                            time.periodStart + startTime / self.timescale_,
                            time.periodStart + currentTime / self.timescale_
                        )
                        cues.append(cue)
                else:
                    log.error(
                        'WVTT sample duration unknown, and no default found!')
                assert not presentation.sampleSize or totalSize <= presentation.sampleSize, 'The samples do not fit evenly into the sample sizes given in the TRUN box!'

                # 检查是不是应该结束循环
                if presentation.sampleSize and totalSize < presentation.sampleSize:
                    continue
                else:
                    break
        assert not reader.hasMoreData(
        ), 'MDAT which contain VTT cues and non-VTT data are not currently supported!'
        # parseVTTC_ 有可能返回的是 None 这里过滤一下
        return [cue for cue in cues if cue]

    @staticmethod
    def parseVTTC_(data: bytes, startTime: float, endTime: float):

        def payl_callback(data: bytes):
            nonlocal payload
            payload = data.decode('utf-8')

        def iden_callback(data: bytes):
            nonlocal _id
            _id = data.decode('utf-8')

        def sttg_callback(data: bytes):
            nonlocal settings
            settings = data.decode('utf-8')

        payload = None
        _id = None
        settings = None

        mp4parser = Mp4Parser()
        mp4parser = mp4parser.box('payl', Mp4Parser.allData(payl_callback))
        mp4parser = mp4parser.box('iden', Mp4Parser.allData(iden_callback))
        mp4parser = mp4parser.box('sttg', Mp4Parser.allData(sttg_callback))
        mp4parser = mp4parser.parse(data)

        if payload:
            return Mp4VttParser.assembleCue_(payload, _id, settings, startTime, endTime)
        else:
            return None

    @staticmethod
    def assembleCue_(payload: bytes, _id: str, settings: str, startTime: float, endTime: float):
        cue = Cue(startTime, endTime, '', _settings=settings)

        styles = {}
        VttTextParser.parseCueStyles(payload, cue, styles)

        if _id:
            cue.id = _id

        # if settings:
        #     # TextParser not fully implemented yet
        #     parser = TextParser(settings)
        #     word = parser.readWord()
        #     while word:
        #         if not VttTextParser.parseCueSetting(cue, word, VTTRegions=[]):
        #             log.warning(f'VTT parser encountered an invalid VTT setting: {word}, The setting will be ignored.')

        #         parser.skipWhitespace()
        #         word = parser.readWord()
        return cue
