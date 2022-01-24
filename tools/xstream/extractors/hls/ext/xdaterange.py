from datetime import datetime
from .x import X


class XDateRange(X):
    '''
    #EXT-X-DATERANGE 第一个分段的绝对时间
    - 2019-01-01T00:00:00.000Z
    '''
    def __init__(self):
        super(XDateRange, self).__init__('#EXT-X-DATERANGE')
        self._id = None # type: str
        self._class = None # type: str
        self.start_date = None # type: datetime
        self.end_date = None # type: datetime
        self.duration = None # type: float
        self.planned_duration = None # type: float
        self.end_on_next = None # type: str
        self.known_attrs = {
            'ID': '_id',
            'CLASS': '_class',
            'START-DATE': self.set_start_date,
            'END-DATE': self.set_end_date,
            'DURATION': self.set_duration,
            'PLANNED-DURATION': self.set_planned_duration,
            'END-ON-NEXT': 'end_on_next',
        }

    def set_duration(self, text: str):
        self.duration = float(text)

    def set_planned_duration(self, text: str):
        self.planned_duration = float(text)

    def get_time(self, text: str):
        if text.endswith('Z') is True:
            text = f'{text[:-1]}+00:00'
        try:
            time = datetime.fromisoformat(text)
        except Exception:
            raise
        return time

    def set_start_date(self, text: str):
        self.start_date = self.get_time(text)

    def set_end_date(self, text: str):
        self.end_date = self.get_time(text)

    def set_attrs_from_line(self, line: str):
        # https://stackoverflow.com/questions/127803
        # datetime.strptime(line, "%Y-%m-%dT%H:%M:%S.%fZ")
        info = self.get_tag_info(line)
        for key, value in self.regex_attrs(info):
            value = value.strip('"')
            if key in self.known_attrs:
                if isinstance(self.known_attrs[key], str):
                    self.__setattr__(self.known_attrs[key], value)
                elif isinstance(self.known_attrs[key], type):
                    self.convert_type(key, value, self.known_attrs[key])
                else:
                    self.known_attrs[key](value)
            elif key.startswith('X-'):
                self.__setattr__(self.format_key(key), value)
            else:
                print(f'unknown attr of {self.TAG_NAME}')
        return self