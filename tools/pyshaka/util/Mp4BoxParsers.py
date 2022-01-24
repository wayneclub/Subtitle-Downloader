from typing import List
from tools.pyshaka.util.DataViewReader import DataViewReader


class ParsedTFHDBox:

    def __init__(self, **kwargs):
        self.trackId = kwargs['trackId']  # type: int
        # type: int
        self.defaultSampleDuration = kwargs['defaultSampleDuration']
        self.defaultSampleSize = kwargs['defaultSampleSize']  # type: int


class ParsedTFDTBox:

    def __init__(self, **kwargs):
        self.baseMediaDecodeTime = kwargs['baseMediaDecodeTime']  # type: int


class ParsedMDHDBox:

    def __init__(self, **kwargs):
        self.timescale = kwargs['timescale']  # type: int


class ParsedTREXBox:

    def __init__(self, **kwargs):
        # type: int
        self.defaultSampleDuration = kwargs['defaultSampleDuration']
        self.defaultSampleSize = kwargs['defaultSampleSize']  # type: int


class ParsedTRUNBox:

    def __init__(self, **kwargs):
        self.sampleCount = kwargs['sampleCount']  # type: int
        self.sampleData = kwargs['sampleData']  # type: List[ParsedTRUNSample]


class ParsedTRUNSample:

    def __init__(self, **kwargs):
        self.sampleDuration = kwargs['sampleDuration']  # type: int
        self.sampleSize = kwargs['sampleSize']  # type: int
        # type: int
        self.sampleCompositionTimeOffset = kwargs['sampleCompositionTimeOffset']


class ParsedTKHDBox:

    def __init__(self, **kwargs):
        self.trackId = kwargs['trackId']  # type: int


class Mp4BoxParsers:

    @staticmethod
    def parseTFHD(reader: DataViewReader, flags: int) -> ParsedTFHDBox:
        defaultSampleDuration = None
        defaultSampleSize = None

        # Read "track_ID"
        trackId = reader.readUint32()

        # Skip "base_data_offset" if present.
        if flags & 0x000001:
            reader.skip(8)

        # Skip "sample_description_index" if present.
        if flags & 0x000002:
            reader.skip(4)

        # Read "default_sample_duration" if present.
        if flags & 0x000008:
            defaultSampleDuration = reader.readUint32()

        # Read "default_sample_size" if present.
        if flags & 0x000010:
            defaultSampleSize = reader.readUint32()

        return ParsedTFHDBox(**{
            'trackId': trackId,
            'defaultSampleDuration': defaultSampleDuration,
            'defaultSampleSize': defaultSampleSize,
        })

    @staticmethod
    def parseTFDT(reader: DataViewReader, version: int) -> ParsedTFDTBox:
        if version == 1:
            baseMediaDecodeTime = reader.readUint64()
        else:
            baseMediaDecodeTime = reader.readUint32()
        return ParsedTFDTBox(**{'baseMediaDecodeTime': baseMediaDecodeTime})

    @staticmethod
    def parseMDHD(reader: DataViewReader, version: int) -> ParsedMDHDBox:
        if version == 1:
            # Skip "creation_time"
            reader.skip(8)
            # Skip "modification_time"
            reader.skip(8)
        else:
            # Skip "creation_time"
            reader.skip(4)
            # Skip "modification_time"
            reader.skip(4)
        timescale = reader.readUint32()
        return ParsedMDHDBox(**{'timescale': timescale})

    @staticmethod
    def parseTREX(reader: DataViewReader) -> ParsedTREXBox:
        pass

    @staticmethod
    def parseTRUN(reader: DataViewReader, version: int, flags: int) -> ParsedTRUNBox:
        sampleCount = reader.readUint32()
        sampleData = []

        # Skip "data_offset" if present.
        if flags & 0x000001:
            reader.skip(4)

        # Skip "first_sample_flags" if present.
        if flags & 0x000004:
            reader.skip(4)

        for _ in range(sampleCount):
            sample = ParsedTRUNSample(**{
                'sampleDuration': None,
                'sampleSize': None,
                'sampleCompositionTimeOffset': None,
            })

            # Read "sample duration" if present.
            if flags & 0x000100:
                sample.sampleDuration = reader.readUint32()

            # Read "sample_size" if present.
            if flags & 0x000200:
                sample.sampleSize = reader.readUint32()

            # Skip "sample_flags" if present.
            if flags & 0x000400:
                reader.skip(4)

            # Read "sample_time_offset" if present.
            if flags & 0x000800:
                if version == 0:
                    sample.sampleCompositionTimeOffset = reader.readUint32()
                else:
                    sample.sampleCompositionTimeOffset = reader.readInt32()
            sampleData.append(sample)

        return ParsedTRUNBox(**{'sampleCount': sampleCount, 'sampleData': sampleData})

    @staticmethod
    def parseTKHD(reader: DataViewReader, version: int) -> ParsedTKHDBox:
        pass
