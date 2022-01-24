import re


class ISMItem(object):
    def __init__(self, name: str = "ISMItem"):
        self.name = name
        self.innertext = ''
        self.childs = []

    def addattr(self, name: str, value):
        self.__setattr__(name, value)

    def addattrs(self, attrs: dict):
        for attr_name, attr_value in attrs.items():
            attr_name: str
            attr_name = attr_name.replace(":", "_")
            self.addattr(attr_name, attr_value)

    def find(self, name: str):
        return [child for child in self.childs if child.name == name]

    def match_duration(self, _duration: str) -> float:
        if isinstance(_duration, str) is False:
            return
        duration = re.match(r"PT(\d+)(\.?\d+)S", _duration)
        if duration is not None:
            return float(duration.group(1)) if duration else 0.0
        # PT23M59.972S
        duration = re.match(r"PT(\d+)M(\d+)(\.?\d+)S", _duration)
        if duration is not None:
            _m, _s, _ss = duration.groups()
            return int(_m) * 60 + int(_s) + float("0" + _ss)
        # P0Y0M0DT0H3M30.000S
        duration = re.match(r"PT(\d+)H(\d+)M(\d+)(\.?\d+)S", _duration.replace('0Y0M0D', ''))
        if duration is not None:
            _h, _m, _s, _ss = duration.groups()
            return int(_h) * 60 * 60 + int(_m) * 60 + int(_s) + float("0" + _ss)
        return 0.0

    def generate(self):
        pass

    def to_int(self, attr_name: str):
        value = self.__getattribute__(attr_name) # type: str
        if isinstance(value, str) and value.isdigit():
            self.__setattr__(attr_name, int(value))