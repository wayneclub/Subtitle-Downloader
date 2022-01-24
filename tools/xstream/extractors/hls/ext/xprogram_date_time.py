from datetime import datetime
from .x import X


class XProgramDateTime(X):
    '''
    #EXT-X-PROGRAM-DATE-TIME 第一个分段的绝对时间
    - 2019-01-01T00:00:00.000Z
    '''
    def __init__(self):
        super(XProgramDateTime, self).__init__('#EXT-X-PROGRAM-DATE-TIME')
        self.program_date_time = None # type: datetime

    def set_attrs_from_line(self, line: str):
        '''
        重写父类同名函数
        '''
        line = self.get_tag_info(line)
        if line.endswith('Z') is True:
            line = f'{line[:-1]}+00:00'
        try:
            self.program_date_time = datetime.fromisoformat(line)
        except Exception:
            raise
        return self