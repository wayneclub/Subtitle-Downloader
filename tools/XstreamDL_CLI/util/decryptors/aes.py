from Crypto.Cipher import AES
from tools.XstreamDL_CLI.models.segment import Segment


class CommonAES:
    '''
    这是一个常规的AES-128-CBC解密类
    或许应该将这个类注册为分段的一个属性？
    '''

    def __init__(self, aes_key: bytes, aes_iv: bytes = None):
        self.aes_key = aes_key  # type: bytes
        self.aes_iv = aes_iv  # type: bytes
        if self.aes_iv is None:
            self.aes_iv = bytes([0] * 16)

    def decrypt(self, segment: Segment) -> bool:
        '''
        解密 落盘
        '''
        try:
            cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_iv)
            content = cipher.decrypt(b''.join(segment.content))
            segment.content = []
        except Exception as e:
            print(f'decrypt {segment.name} error -> {e}')
            return False
        else:
            segment.get_path().write_bytes(content)
            return True
