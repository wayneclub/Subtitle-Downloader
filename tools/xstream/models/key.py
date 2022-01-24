class StreamKey:
    '''
    一条流的加密信息 含有下列属性
    - 加密方法
    - key的uri
    - key内容
    - keyid
    - 偏移量
    - 其他属性 -> 根据流类型而定
    含有下面的方法
    - 设置key内容
    - 设置iv
    - 保存为文本
    - 从文本加载
    '''
    def __init__(self):
        self.method = 'AES-128' # type: str
        self.uri = None # type: str
        self.key = b'' # type: bytes
        self.keyid = None # type: str
        self.iv = '0' * 32 # type: str

    def set_key(self, key: bytes):
        self.key = key
        return self

    def set_iv(self, iv: str):
        if iv is None:
            return
        self.iv = iv
        return self

    def dump(self):
        pass

    def load(self):
        pass