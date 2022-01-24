import re
import time
from typing import List
from pathlib import Path
from tools.xstream.models.stream import Stream
from tools.xstream.models.base import BaseUri
from tools.xstream.extractors.mss.segment import MSSSegment
from tools.xstream.extractors.mss.box_util import (
    u8,
    u16,
    u1616,
    u32,
    u64,
    s88,
    s16,
    s1616,
    box,
    full_box,
    unity_matrix,
    extract_box_data,
)

TRACK_ENABLED = 0x1
TRACK_IN_MOVIE = 0x2
TRACK_IN_PREVIEW = 0x4

SELF_CONTAINED = 0x1

NALUTYPE_SPS = 7
NALUTYPE_PPS = 8


class MSSStream(Stream):
    def __init__(self, index: int, uri_item: BaseUri, save_dir: Path):
        super(MSSStream, self).__init__(index, uri_item, save_dir)
        self.model = 'mss'
        self.timescale = 10000000
        self.channels = 2
        self.bits_per_sample = 16
        self.sampling_rate = 16
        self.codec_private_data = None  # type: str
        self.nal_unit_length_field = 4
        self.segments = []  # type: List[MSSSegment]
        self.suffix = '.mp4'
        self.has_init_segment = False
        self.skey = ''  # type: str
        self.kid = bytes([0] * 16)
        self.track_index = 0
        self.width = self.height = 0
        self.set_init_segment()
        self.append_segment()

    def set_kid(self, kid: bytes):
        self.kid = kid

    def get_name(self):
        if self.stream_type != '':
            base_name = f'{self.name}_{self.stream_type}'
        else:
            base_name = self.name
        if self.codecs is not None:
            base_name += f'_{self.codecs}'
        if self.stream_type == 'text' and self.lang != '':
            base_name += f'_{self.lang}'
        elif self.stream_type == 'video' and self.resolution != '':
            base_name += f'_{self.resolution}'
        elif self.stream_type == 'audio' and self.lang != '':
            base_name += f'_{self.lang}'
        if self.stream_type in ['audio', 'video'] and self.bandwidth is not None:
            base_name += f'_{self.bandwidth / 1000:.2f}kbps'
        return base_name

    def get_ism_params(self):
        height_width = self.resolution.split('x')
        if len(height_width) == 2:
            height, width = height_width
        else:
            height, width = 0, 0
        return {
            'fourcc': self.codecs,
            'duration': int(self.duration),
            'timescale': self.timescale,
            'language': 'und' if self.lang == '' else self.lang,
            'height': int(height),
            'width': int(width),
            'stream_type': self.stream_type,
            'channels': self.channels,
            'bits_per_sample': self.bits_per_sample,
            'sampling_rate': self.sampling_rate,
            'codec_private_data': self.codec_private_data,
            'nal_unit_length_field': self.nal_unit_length_field,
        }

    def set_init_segment(self):
        self.has_init_segment = True
        segment = MSSSegment().set_index(-1).set_folder(self.save_dir)
        self.segments.append(segment)

    def append_segment(self):
        index = len(self.segments)
        if self.has_init_segment:
            index -= 1
        segment = MSSSegment().set_index(index).set_folder(self.save_dir)
        self.segments.append(segment)

    def update(self, stream: 'MSSStream'):
        '''
        Representation id相同可以合并
        这个时候应该重新计算时长和码率
        '''
        total_duration = self.duration + stream.duration
        if total_duration > 0:
            self.bandwidth = (stream.duration * stream.bandwidth + self.duration *
                              self.bandwidth) / (self.duration + stream.duration)
        self.duration += stream.duration
        for segment in stream.segments:
            # 被合并的流的init分段 避免索引计算错误
            if segment.segment_type == 'init':
                stream.segments.remove(segment)
                break
        self.segments_extend(stream.segments)

    def set_subtitle_url(self, url: str):
        self.has_init_segment = True
        self.segments[-1].set_subtitle_url(self.fix_url(url))
        # self.append_segment()

    def set_init_url(self, url: str):
        self.has_init_segment = True
        self.segments[-1].set_init_url(self.fix_url(url))
        self.append_segment()

    def set_media_url(self, url: str):
        self.segments[-1].set_media_url(self.fix_url(url))
        self.append_segment()

    def set_segment_duration(self, duration: float):
        self.segments[-1].set_duration(duration)

    def set_segments_duration(self, duration: float):
        '''' init分段没有时长 这里只用设置普通分段的 '''
        for segment in self.segments:
            segment.set_duration(duration)

    def set_protection_flag(self, flag: bool):
        for segment in self.segments:
            segment.set_protection_flag(flag)

    def set_lang(self, lang: str):
        if lang is None:
            return
        self.lang = lang.lower()

    def set_bandwidth(self, bandwidth: int):
        self.bandwidth = bandwidth

    def set_codecs(self, codecs: str):
        if re.match('avc(1|3)*', codecs.lower()):
            codecs = 'H264'
        if re.match('(hev|hvc)1*', codecs.lower()):
            codecs = 'H265'
        if re.match('vp(09|9)*', codecs.lower()):
            codecs = 'VP9'
        if codecs != 'AACL' and re.match('aac*', codecs.lower()):
            codecs = 'AAC'
        if codecs.lower() in ['wvtt', 'ttml']:
            codecs = codecs.upper()
        self.codecs = codecs

    def set_resolution(self, width: str, height: str):
        if width is None or height is None:
            return
        self.width = int(width)
        self.height = int(height)
        self.resolution = f'{width}x{height}'

    def set_stream_type(self, stream_type: str):
        if stream_type is None:
            return
        self.stream_type = stream_type
        if self.stream_type == 'audio':
            self.suffix = '.m4a'

    def set_track_index(self, track_index: int):
        ''' to calc track id '''
        self.track_index = track_index

    def get_track_name(self):
        if self.track_name:
            return f'{self.track_name}_{self.track_index}'
        else:
            return f'{self.stream_type}_{self.track_index}'

    def set_track_name(self, track_name: str):
        self.track_name = track_name

    def set_timescale(self, timescale: int):
        if timescale is None:
            return
        self.timescale = timescale

    def set_bits_per_sample(self, bits_per_sample: str):
        if bits_per_sample is None:
            return
        self.bits_per_sample = bits_per_sample

    def set_sampling_rate(self, sampling_rate: str):
        if sampling_rate is None:
            return
        self.sampling_rate = sampling_rate

    def set_channels(self, channels: str):
        if channels is None:
            return
        self.channels = channels

    def set_codec_private_data(self, codec_private_data: str):
        if codec_private_data is None:
            return
        self.codec_private_data = codec_private_data

    def set_nal_unit_length_field(self, nal_unit_length_field: int):
        if nal_unit_length_field is None:
            return
        self.nal_unit_length_field = nal_unit_length_field

    def fix_header(self, is_fake: bool):
        if is_fake:
            track_id = 1
        else:
            tfhd_data = extract_box_data(self.segments[1].get_path().read_bytes(), [
                                         b'moof', b'traf', b'tfhd'])
            track_id = u32.unpack(tfhd_data[4:8])[0]
        init_payload = self.write_iso6_header(
            track_id, is_enc=self.segments[0].has_protection)
        self.segments[0].get_path().write_bytes(init_payload)

    def get_sinf_payload(self, kid: bytes, codec: bytes):
        sinf_payload = box(b'frma', codec)

        # scheme_type 'cenc' => common encryption
        schm_payload = u32.pack(0x63656E63)
        # scheme_version Major version 1, Minor version 0
        schm_payload += u32.pack(0x00010000)
        sinf_payload += full_box(b'schm', 0, 0, schm_payload)

        tenc_payload = u8.pack(0x0) * 2
        tenc_payload += u8.pack(0x1)  # default_IsEncrypted
        tenc_payload += u8.pack(0x8)  # default_IV_size
        tenc_payload += kid  # default_KID
        tenc_payload = full_box(b'tenc', 0, 0, tenc_payload)
        sinf_payload += box(b'schi', tenc_payload)
        sinf_payload = box(b'sinf', sinf_payload)
        return sinf_payload

    def write_iso6_header(self, track_id: int, write_time: bool = False, is_enc: bool = False):
        '''
        根据dashif的信息，需要以下信息构成ism的init数据
        - track_name
        - track_id
        - FourCC
        - duration
        - timescale
        - language
        - height 仅视频
        - width 仅视频
        - bandwidth
        - kid
        - 是否加密
        - 类型
        '''
        if write_time:
            creation_time = modification_time = int(time.time())
        else:
            creation_time = modification_time = 0
        track_name = self.get_track_name()
        fourcc = self.codecs
        duration = self.duration
        timescale = self.timescale
        language = 'und' if self.lang == '' else self.lang
        height = self.height
        width = self.width
        bandwidth = self.bandwidth
        kid = self.kid
        stream_type = self.stream_type
        channels = self.channels
        bits_per_sample = self.bits_per_sample
        sampling_rate = self.sampling_rate
        codec_private_data = self.codec_private_data

        # ftyp box
        ftyp_payload = b'iso6'  # major brand
        ftyp_payload += u32.pack(1)  # minor version
        ftyp_payload += b'isom' + b'iso6' + b'msdh'  # compatible brands

        mvhd_payload = u64.pack(creation_time)
        mvhd_payload += u64.pack(modification_time)
        mvhd_payload += u32.pack(timescale)
        mvhd_payload += u64.pack(int(duration * timescale))
        mvhd_payload += s1616.pack(1)  # rate
        mvhd_payload += s88.pack(1)  # volume
        mvhd_payload += u16.pack(0)  # reserved1
        mvhd_payload += u32.pack(0) * 2  # reserved2
        mvhd_payload += unity_matrix
        mvhd_payload += u32.pack(0) * 6  # pre defined
        # 需要确认是不是要 +1
        mvhd_payload += u32.pack(track_id + 1)  # next track id
        moov_payload = full_box(
            b'mvhd', 1, 0, mvhd_payload)  # Movie Header Box

        tkhd_payload = u64.pack(creation_time)
        tkhd_payload += u64.pack(modification_time)
        tkhd_payload += u32.pack(track_id)  # track id
        tkhd_payload += u32.pack(0)  # reserved1
        tkhd_payload += u64.pack(int(duration * timescale))
        tkhd_payload += u32.pack(0) * 2  # reserved2
        tkhd_payload += s16.pack(0)  # layer
        tkhd_payload += s16.pack(0)  # alternate group
        # 1.0 ???
        tkhd_payload += s88.pack(1)  # volume
        tkhd_payload += u16.pack(0)  # reserved3
        tkhd_payload += unity_matrix
        tkhd_payload += u1616.pack(width)
        tkhd_payload += u1616.pack(height)
        trak_payload = full_box(b'tkhd', 1, TRACK_ENABLED | TRACK_IN_MOVIE |
                                TRACK_IN_PREVIEW, tkhd_payload)  # Track Header Box

        mdhd_payload = u64.pack(creation_time)
        mdhd_payload += u64.pack(modification_time)
        mdhd_payload += u32.pack(timescale)
        mdhd_payload += u64.pack(int(duration * timescale))
        mdhd_payload += u16.pack(((ord(language[0]) - 0x60) << 10) | (
            (ord(language[1]) - 0x60) << 5) | (ord(language[2]) - 0x60))
        mdhd_payload += u16.pack(0)  # pre defined
        mdia_payload = full_box(
            b'mdhd', 1, 0, mdhd_payload)  # Media Header Box

        hdlr_payload = u32.pack(0)  # pre defined
        if stream_type == 'video':  # handler type
            hdlr_payload += b'vide'
        elif stream_type == 'audio':
            hdlr_payload += b'soun'
        elif stream_type == 'text':
            hdlr_payload += b'subt'
        else:
            hdlr_payload += b'meta'
            assert False
        hdlr_payload += u32.pack(0) * 3  # reserved
        hdlr_payload += track_name.encode('utf-8') + b'\0'  # name
        # Handler Reference Box
        mdia_payload += full_box(b'hdlr', 0, 0, hdlr_payload)

        if stream_type == 'video':
            vmhd_payload = u16.pack(0)  # graphics mode
            vmhd_payload += u16.pack(0) * 3  # opcolor
            media_header_box = full_box(
                b'vmhd', 0, 1, vmhd_payload)  # Video Media Header
        elif stream_type == 'audio':
            smhd_payload = s88.pack(0)  # balance
            smhd_payload += u16.pack(0)  # reserved
            media_header_box = full_box(
                b'smhd', 0, 1, smhd_payload)  # Sound Media Header
        elif stream_type == 'text':
            media_header_box = full_box(
                b'sthd', 0, 1, b'')  # Subtitle Media Header
        else:
            assert False
        minf_payload = media_header_box

        dref_payload = u32.pack(1)  # entry count
        # Data Entry URL Box
        dref_payload += full_box(b'url ', 0, SELF_CONTAINED, b'')
        dinf_payload = full_box(
            b'dref', 0, 0, dref_payload)  # Data Reference Box
        minf_payload += box(b'dinf', dinf_payload)  # Data Information Box

        stsd_payload = u32.pack(1)  # entry count

        sample_entry_payload = u8.pack(0) * 6  # reserved1
        sample_entry_payload += u16.pack(1)  # data reference index
        if stream_type == 'audio':
            sample_entry_payload += u32.pack(0) * 2  # reserved2
            sample_entry_payload += u16.pack(channels)
            sample_entry_payload += u16.pack(bits_per_sample)
            sample_entry_payload += u16.pack(0)  # pre defined
            sample_entry_payload += u16.pack(0)  # reserved3
            # 不管这里多少 mediainfo 查看出来的都是正确的数值 可能通过其他部分计算
            sample_entry_payload += u1616.pack(sampling_rate)

            audioSpecificConfig = bytes.fromhex(codec_private_data)

            # ESDS length = esds box header length (= 12) +
            #               ES_Descriptor header length (= 5) +
            #               DecoderConfigDescriptor header length (= 15) +
            #               decoderSpecificInfo header length (= 2) +
            #               AudioSpecificConfig length (= codecPrivateData length)
            # esdsLength = 34 + len(audioSpecificConfig)

            # ES_Descriptor (see ISO/IEC 14496-1 (Systems))
            esds_payload = u8.pack(0x03)  # tag = 0x03 (ES_DescrTag)
            esds_payload += u8.pack(20 + len(audioSpecificConfig))  # size
            esds_payload += u8.pack((track_id & 0xFF00)
                                    >> 8)  # ES_ID = track_id
            esds_payload += u8.pack(track_id & 0x00FF)
            esds_payload += u8.pack(0)  # flags and streamPriority

            # DecoderConfigDescriptor (see ISO/IEC 14496-1 (Systems))
            esds_payload += u8.pack(0x04)  # tag = 0x04 (DecoderConfigDescrTag)
            esds_payload += u8.pack(15 + len(audioSpecificConfig))  # size
            # objectTypeIndication = 0x40 (MPEG-4 AAC)
            esds_payload += u8.pack(0x40)
            # esds_payload[i] = 0x05 << 2 # streamType = 0x05 (Audiostream)
            # esds_payload[i] |= 0 << 1 # upStream = 0
            esds_payload += u8.pack((0x05 << 2) | (0 << 1) | 1)  # reserved = 1
            esds_payload += u8.pack(0xFF)  # buffersizeDB = undefined
            esds_payload += u8.pack(0xFF)  # ''
            esds_payload += u8.pack(0xFF)  # ''
            # maxBitrate
            esds_payload += u8.pack((bandwidth & 0xFF000000) >> 24)
            esds_payload += u8.pack((bandwidth & 0x00FF0000) >> 16)  # ''
            esds_payload += u8.pack((bandwidth & 0x0000FF00) >> 8)  # ''
            esds_payload += u8.pack((bandwidth & 0x000000FF))  # ''
            # avgbitrate
            esds_payload += u8.pack((bandwidth & 0xFF000000) >> 24)
            esds_payload += u8.pack((bandwidth & 0x00FF0000) >> 16)  # ''
            esds_payload += u8.pack((bandwidth & 0x0000FF00) >> 8)  # ''
            esds_payload += u8.pack((bandwidth & 0x000000FF))  # ''

            # DecoderSpecificInfo (see ISO/IEC 14496-1 (Systems))
            esds_payload += u8.pack(0x05)  # tag = 0x05 (DecSpecificInfoTag)
            esds_payload += u8.pack(len(audioSpecificConfig))  # size
            esds_payload += audioSpecificConfig  # AudioSpecificConfig bytes
            if is_enc:
                sample_entry_payload += full_box(
                    b'esds', 0, 0, esds_payload) + self.get_sinf_payload(kid, b'mp4a')
                sample_entry_box = box(b'enca', sample_entry_payload)
            else:
                sample_entry_payload += full_box(b'esds', 0, 0, esds_payload)
                sample_entry_box = box(b'mp4a', sample_entry_payload)
        elif stream_type == 'video':
            sample_entry_payload += u16.pack(0)  # pre defined
            sample_entry_payload += u16.pack(0)  # reserved
            sample_entry_payload += u32.pack(0) * 3  # pre defined
            sample_entry_payload += u16.pack(width)
            sample_entry_payload += u16.pack(height)
            sample_entry_payload += u1616.pack(0x48)  # horiz resolution 72 dpi
            sample_entry_payload += u1616.pack(0x48)  # vert resolution 72 dpi
            sample_entry_payload += u32.pack(0)  # reserved
            sample_entry_payload += u16.pack(1)  # frame count
            # sample_entry_payload += u8.pack(0) * 32 # compressor name
            sample_entry_payload += bytes([
                0x0A, 0x41, 0x56, 0x43, 0x20, 0x43, 0x6F, 0x64,
                0x69, 0x6E, 0x67, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])  # compressor name
            sample_entry_payload += u16.pack(0x18)  # depth
            sample_entry_payload += u16.pack(65535)  # pre defined3

            if fourcc in ('H264', 'AVC1'):
                # avcCLength = 15
                sps = []
                pps = []
                nalus = codec_private_data.split('00000001')[1:]
                for nalu in nalus:
                    naluBytes = bytes.fromhex(nalu)
                    naluType = naluBytes[0] & 0x1F
                    if naluType == NALUTYPE_SPS:
                        sps.append(naluBytes)
                        # avcCLength += len(naluBytes) + 2 # 2 = sequenceParameterSetLength field length
                    elif naluType == NALUTYPE_PPS:
                        # avcCLength += len(naluBytes) + 2 # 2 = pictureParameterSetLength field length
                        pps.append(naluBytes)
                    else:
                        pass
                if len(sps) > 0:
                    AVCProfileIndication = sps[0][1]
                    profile_compatibility = sps[0][2]
                    AVCLevelIndication = sps[0][3]
                else:
                    AVCProfileIndication = 0
                    profile_compatibility = 0
                    AVCLevelIndication = 0
                # 这里不知道为什么没用上
                # avcc_head_payload = bytes([
                #     (avcCLength & 0xFF000000) >> 24,
                #     (avcCLength & 0x00FF0000) >> 16,
                #     (avcCLength & 0x0000FF00) >> 8,
                #     (avcCLength & 0x000000FF),
                # ])

                avcc_payload = u8.pack(1)  # configurationVersion = 1
                avcc_payload += u8.pack(AVCProfileIndication)
                avcc_payload += u8.pack(profile_compatibility)
                avcc_payload += u8.pack(AVCLevelIndication)
                # '11111' + lengthSizeMinusOne = 3
                avcc_payload += u8.pack(0xFF)
                # '111' + numOfSequenceParameterSets
                avcc_payload += u8.pack(0xE0 | len(sps))
                for item in sps:
                    avcc_payload += u8.pack((len(item) & 0xFF00) >> 8)
                    avcc_payload += u8.pack((len(item) & 0x00FF))
                    avcc_payload += item
                avcc_payload += u8.pack(len(pps))  # numOfPictureParameterSets
                for item in pps:
                    avcc_payload += u8.pack((len(item) & 0xFF00) >> 8)
                    avcc_payload += u8.pack((len(item) & 0x00FF))
                    avcc_payload += item

                # AVC Decoder Configuration Record
                sample_entry_payload += box(b'avcC', avcc_payload) + \
                    self.get_sinf_payload(kid, b'avc1')
                sample_entry_box = box(
                    b'encv', sample_entry_payload)  # AVC Simple Entry
            else:
                assert False
        elif stream_type == 'text':
            if fourcc == 'TTML':
                sample_entry_payload += b'http://www.w3.org/ns/ttml\0'  # namespace
                sample_entry_payload += b'\0'  # schema location
                sample_entry_payload += b'\0'  # auxilary mime types(??)
                sample_entry_box = box(b'stpp', sample_entry_payload)
            else:
                assert False
        else:
            assert False

        stts_payload = u32.pack(0)  # entry count
        # Decoding Time to Sample Box
        stbl_payload = full_box(b'stts', 0, 0, stts_payload)

        stsc_payload = u32.pack(0)  # entry count
        # Sample To Chunk Box
        stbl_payload += full_box(b'stsc', 0, 0, stsc_payload)

        stco_payload = u32.pack(0)  # entry count
        # Chunk Offset Box
        stbl_payload += full_box(b'stco', 0, 0, stco_payload)

        stsz_payload = u32.pack(0) + u32.pack(0)  # sample size, sample count
        # Sample Size Box
        stbl_payload += full_box(b'stsz', 0, 0, stsz_payload)

        stsd_payload += sample_entry_box
        # Sample Description Box
        stbl_payload += full_box(b'stsd', 0, 0, stsd_payload)

        minf_payload += box(b'stbl', stbl_payload)  # Sample Table Box
        mdia_payload += box(b'minf', minf_payload)  # Media Information Box
        trak_payload += box(b'mdia', mdia_payload)  # Media Box
        moov_payload += box(b'trak', trak_payload)  # Track Box

        trex_payload = u32.pack(track_id)  # track id
        trex_payload += u32.pack(1)  # default sample description index
        trex_payload += u32.pack(0)  # default sample duration
        trex_payload += u32.pack(0)  # default sample size
        trex_payload += u32.pack(0)  # default sample flags
        mvex_payload = full_box(
            b'trex', 0, 0, trex_payload)  # Track Extends Box
        moov_payload += box(b'mvex', mvex_payload)  # Movie Extends Box
        moov_payload = box(b'moov', moov_payload)
        moov_payload = box(b'ftyp', ftyp_payload) + moov_payload
        return moov_payload
