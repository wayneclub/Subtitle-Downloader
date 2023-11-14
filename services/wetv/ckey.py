from ctypes import c_int32


class CKey:
    def __init__(self):
        self.encryption_arrays = [[
            1332468387, -1641050960, 2136896045, -1629555948,
            1399201960, -850809832, -1307058635, 751381793,
            -1933648423, 1106735553, -203378700, -550927659,
            766369351, 1817882502, -1615200142, 1083409063,
            -104955314, -1780208184, 173944250, 1254993693,
            1422337688, -1054667952, -880990486, -2119136777,
            -1822404972, 1380140484, -1723964626, 412019417,
            -890799303, -1734066435, 26893779, 420787978,
            -1337058067, 686432784, 695238595, 811911369,
            -391724567, -1068702727, -381903814, -648522509,
            -1266234148, 1959407397, -1644776673, 1152313324]]
        d = [None] * 256
        f = d.copy()
        g = d.copy()
        h = d.copy()
        j = d.copy()
        o = d.copy()
        for i in range(256):
            o[i] = i << 1 if i < 128 else i << 1 ^ 283

        t = 0
        u = 0
        for i in range(256):
            v = u ^ u << 1 ^ u << 2 ^ u << 3 ^ u << 4
            v = CKey.rshift(v, 8) ^ 255 & v ^ 99
            d[t] = v
            x = o[t]
            z = o[o[x]]
            A = CKey.int32(257 * o[v] ^ 16843008 * v)
            f[t] = CKey.int32(A << 24 | CKey.rshift(A, 8))
            g[t] = CKey.int32(A << 16 | CKey.rshift(A, 16))
            h[t] = CKey.int32(A << 8 | CKey.rshift(A, 24))
            j[t] = A
            if t == 0:
                t = 1
                u = 1
            else:
                t = x ^ o[o[o[z ^ x]]]
                u ^= o[o[u]]

        self.encryption_arrays.append(f)
        self.encryption_arrays.append(g)
        self.encryption_arrays.append(h)
        self.encryption_arrays.append(j)
        self.encryption_arrays.append(d)

    @staticmethod
    def rshift(val, n):
        return (val & 0xFFFFFFFF) >> n

    @staticmethod
    def int32(val):
        return c_int32(val).value

    @staticmethod
    def encode_text(text):
        length = len(text)
        arr = [0] * (length // 4)
        for i in range(length):
            arr[i // 4] |= (255 & ord(text[i])) << 24 - i % 4 * 8
        return arr, length

    @staticmethod
    def decode_text(arr, length):
        text_array = []
        for i in range(length):
            text_array.append('{:02x}'.format(
                CKey.rshift(arr[i // 4], 24 - i % 4 * 8) & 255))

        return ''.join(text_array)

    @staticmethod
    def calculate_hash(text):
        result = 0
        for char in text:
            result = CKey.int32(result << 5) - result + ord(char)
        return str(result)

    @staticmethod
    def pad_text(text):
        pad_length = 16 - len(text) % 16
        return text + chr(pad_length) * pad_length

    def encrypt(self, arr):
        for i in range(0, len(arr), 4):
            self.main_algorithm(arr, i)

    def main_algorithm(self, a, b):
        c, d, e, f, g, h = self.encryption_arrays

        if b == 0:
            xor_arr = [22039283, 1457920463, 776125350, -1941999367]
        else:
            xor_arr = a[b - 4: b]

        for i, val in enumerate(xor_arr):
            a[b + i] ^= val

        j = a[b] ^ c[0]
        k = a[b + 1] ^ c[1]
        l = a[b + 2] ^ c[2]
        m = a[b + 3] ^ c[3]
        n = 4
        for _ in range(9):
            q = (d[CKey.rshift(j, 24)] ^ e[CKey.rshift(k, 16) & 255]
                 ^ f[CKey.rshift(l, 8) & 255] ^ g[255 & m] ^ c[n])
            s = (d[CKey.rshift(k, 24)] ^ e[CKey.rshift(l, 16) & 255]
                 ^ f[CKey.rshift(m, 8) & 255] ^ g[255 & j] ^ c[n + 1])
            t = (d[CKey.rshift(l, 24)] ^ e[CKey.rshift(m, 16) & 255]
                 ^ f[CKey.rshift(j, 8) & 255] ^ g[255 & k] ^ c[n + 2])
            m = (d[CKey.rshift(m, 24)] ^ e[CKey.rshift(j, 16) & 255]
                 ^ f[CKey.rshift(k, 8) & 255] ^ g[255 & l] ^ c[n + 3])
            j = q
            k = s
            l = t
            n += 4

        q = CKey.int32(h[CKey.rshift(j, 24)] << 24
                       | h[CKey.rshift(k, 16) & 255] << 16
                       | h[CKey.rshift(l, 8) & 255] << 8
                       | h[255 & m]) ^ c[n]
        s = CKey.int32(h[CKey.rshift(k, 24)] << 24
                       | h[CKey.rshift(l, 16) & 255] << 16
                       | h[CKey.rshift(m, 8) & 255] << 8
                       | h[255 & j]) ^ c[n + 1]
        t = CKey.int32(h[CKey.rshift(l, 24)] << 24
                       | h[CKey.rshift(m, 16) & 255] << 16
                       | h[CKey.rshift(j, 8) & 255] << 8
                       | h[255 & k]) ^ c[n + 2]
        m = CKey.int32(h[CKey.rshift(m, 24)] << 24
                       | h[CKey.rshift(j, 16) & 255] << 16
                       | h[CKey.rshift(k, 8) & 255] << 8
                       | h[255 & l]) ^ c[n + 3]
        a[b] = q
        a[b + 1] = s
        a[b + 2] = t
        a[b + 3] = m

    def make(self, vid, tm, app_ver, guid, platform, url,
             # user_agent is shortened anyway
             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
             referer='', nav_code_name='Mozilla',
             nav_name='Netscape', nav_platform='Win64'):
        text_parts = [
            '', vid, tm, 'mg3c3b04ba', app_ver, guid, platform,
            url[:48], user_agent[:48].lower(), referer[:48],
            nav_code_name, nav_name, nav_platform, '00', ''
        ]
        text_parts.insert(1, CKey.calculate_hash('|'.join(text_parts)))

        text = CKey.pad_text('|'.join(text_parts))
        [arr, length] = CKey.encode_text(text)
        self.encrypt(arr)
        return CKey.decode_text(arr, length).upper()
