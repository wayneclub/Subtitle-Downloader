import io
import struct

u8 = struct.Struct('>B')
u88 = struct.Struct('>Bx')
u16 = struct.Struct('>H')
u1616 = struct.Struct('>Hxx')
u32 = struct.Struct('>I')
u64 = struct.Struct('>Q')

s88 = struct.Struct('>bx')
s16 = struct.Struct('>h')
s1616 = struct.Struct('>hxx')
s32 = struct.Struct('>i')
unity_matrix = (s32.pack(0x10000) + s32.pack(0) * 3) * 2 + s32.pack(0x40000000)


def box(box_type, payload):
    return u32.pack(8 + len(payload)) + box_type + payload


def full_box(box_type, version, flags, payload):
    return box(box_type, u8.pack(version) + u32.pack(flags)[1:] + payload)


def extract_box_data(data: bytes, box_sequence: list):
    data_reader = io.BytesIO(data)
    while True:
        box_size = u32.unpack(data_reader.read(4))[0]
        box_type = data_reader.read(4)
        if box_type == box_sequence[0]:
            box_data = data_reader.read(box_size - 8)
            if len(box_sequence) == 1:
                return box_data
            return extract_box_data(box_data, box_sequence[1:])
        data_reader.seek(box_size - 8, 1)