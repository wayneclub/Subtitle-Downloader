class TimeContext:
    def __init__(self, **kwargs):
        self.periodStart = kwargs['periodStart'] # tpye: float
        self.segmentStart = kwargs['segmentStart'] # tpye: float
        self.segmentEnd = kwargs['segmentEnd'] # tpye: float


class TextParser:

    def __init__(self, data: str):
        self.data_ = data
        self.position_ = 0

    def atEnd(self):
        return self.position_ == len(self.data_)

    def readLine(self):
        assert 1 == 0, 'not implemented yet'

    def readWord(self):
        assert 1 == 0, 'not implemented yet'

    def readRegexReturnCapture_(self, regex: str, index: int):
        if self.atEnd():
            return None
        ret = self.readRegex(regex)
        if not ret:
            return None
        else:
            return ret[index]

    def readRegex(self, regex: str):
        index = self.indexOf_(regex)
        if self.atEnd() or index is None or index.position != self.position_:
            return None

        self.position_ += index.length
        return index.results

    def indexOf_(self, regex: str):
        assert 1 == 0, 'not implemented yet'