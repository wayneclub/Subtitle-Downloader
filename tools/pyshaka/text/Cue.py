from enum import Enum


class positionAlign(Enum):
    LEFT = 'line-left'
    RIGHT = 'line-right'
    CENTER = 'center'
    AUTO = 'auto'


class textAlign(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'
    START = 'start'
    END = 'end'


class displayAlign(Enum):
    BEFORE = 'before'
    CENTER = 'center'
    AFTER = 'after'


class direction(Enum):
    HORIZONTAL_LEFT_TO_RIGHT = 'ltr'
    HORIZONTAL_RIGHT_TO_LEFT = 'rtl'


class writingMode(Enum):
    HORIZONTAL_TOP_TO_BOTTOM = 'horizontal-tb'
    VERTICAL_LEFT_TO_RIGHT = 'vertical-lr'
    VERTICAL_RIGHT_TO_LEFT = 'vertical-rl'


class lineInterpretation(Enum):
    LINE_NUMBER = 0
    PERCENTAGE = 1


class lineAlign(Enum):
    CENTER = 'center'
    START = 'start'
    END = 'end'


class defaultTextColor(Enum):
    white = '#FFF'
    lime = '#0F0'
    cyan = '#0FF'
    red = '#F00'
    yellow = '#FF0'
    magenta = '#F0F'
    blue = '#00F'
    black = '#000'


class defaultTextBackgroundColor(Enum):
    bg_white = '#FFF'
    bg_lime = '#0F0'
    bg_cyan = '#0FF'
    bg_red = '#F00'
    bg_yellow = '#FF0'
    bg_magenta = '#F0F'
    bg_blue = '#00F'
    bg_black = '#000'


class fontWeight(Enum):
    NORMAL = 400
    BOLD = 700


class fontStyle(Enum):
    NORMAL = 'normal'
    ITALIC = 'italic'
    OBLIQUE = 'oblique'


class textDecoration(Enum):
    UNDERLINE = 'underline'
    LINE_THROUGH = 'lineThrough'
    OVERLINE = 'overline'


class Cue:

    def __init__(self, startTime: float, endTime: float, payload: str):
        self.startTime = startTime
        self.direction = direction.HORIZONTAL_LEFT_TO_RIGHT
        self.endTime = endTime
        self.payload = payload
        self.region = CueRegion()
        self.position = None
        self.positionAlign = positionAlign.AUTO
        self.size = 0
        self.textAlign = textAlign.CENTER
        self.writingMode = writingMode.HORIZONTAL_TOP_TO_BOTTOM
        self.lineInterpretation = lineInterpretation.LINE_NUMBER
        self.line = None
        self.lineHeight = ''
        self.lineAlign = lineAlign.START
        self.displayAlign = displayAlign.AFTER
        self.color = ''
        self.backgroundColor = ''
        self.backgroundImage = ''
        self.border = ''
        self.fontSize = ''
        self.fontWeight = fontWeight.NORMAL
        self.fontStyle = fontStyle.NORMAL
        self.fontFamily = ''
        self.letterSpacing = ''
        self.linePadding = ''
        self.opacity = 1
        self.textDecoration = []
        self.wrapLine = True
        self.id = ''
        self.nestedCues = []
        self.lineBreak = False
        self.spacer = False
        self.cellResolution = {'columns': 32, 'rows': 15}

    @staticmethod
    def lineBreak(start: float, end: float) -> 'Cue':
        cue = Cue(start, end, '')
        cue.lineBreak = True
        return cue

    def clone(self):
        cue = Cue(0, 0, '')
        for k, v in self.__dict__.items():
            if isinstance(v, list):
                v = v.copy()
            cue.__setattr__(k, v)
        return cue

    @staticmethod
    def equal(cue1: 'Cue', cue2: 'Cue') -> bool:
        if cue1.startTime != cue2.startTime or cue1.endTime != cue2.endTime or cue1.payload != cue2.payload:
            return False
        for k, v in cue1.__dict__.items():
            if k == 'startTime' or k == 'endTime' or k == 'payload':
                pass
            elif k == 'nestedCues':
                if not Cue.equal(cue1.nestedCues, cue2.nestedCues):
                    return False
            elif k == 'region' or k == 'cellResolution':
                for k2 in cue1.__getattribute__(k):
                    if cue1.__getattribute__(k)[k2] != cue2.__getattribute__(k)[k2]:
                        return False
            elif isinstance(cue1.__getattribute__(k), list):
                if cue1.__getattribute__(k) != cue2.__getattribute__(k):
                    return False
            else:
                if cue1.__getattribute__(k) != cue1.__getattribute__(k):
                    return False
        return True


class units(Enum):
    PX = 0
    PERCENTAGE = 1
    LINES = 2


class scrollMode(Enum):
    NONE = ''
    UP = 'up'


class CueRegion:

    def __init__(self, **kwargs):
        self.id = ''
        self.viewportAnchorX = 0
        self.viewportAnchorY = 0
        self.regionAnchorX = 0
        self.regionAnchorY = 0
        self.width = 100
        self.height = 100
        self.heightUnits = units.PERCENTAGE
        self.widthUnits = units.PERCENTAGE
        self.viewportAnchorUnits = units.PERCENTAGE
        self.scroll = scrollMode.NONE