from tools.XstreamDL_CLI.extractors.metaitem import MetaItem


class ISMItem(MetaItem):
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

    def to_int(self, attr_name: str):
        value = self.__getattribute__(attr_name)  # type: str
        if isinstance(value, str) and value.isdigit():
            self.__setattr__(attr_name, int(value))
