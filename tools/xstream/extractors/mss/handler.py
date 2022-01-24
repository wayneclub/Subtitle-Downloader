from xml.parsers.expat import ParserCreate
from .ism import ISM
from .childs.c import c
from .childs.protection import Protection
from .childs.protectionheader import ProtectionHeader
from .childs.qualitylevel import QualityLevel
from .childs.streamindex import StreamIndex


def xml_handler(content: str):
    def handle_start_element(tag, attrs):
        nonlocal ism
        nonlocal ism_handlers
        if ism is None:
            if tag != 'SmoothStreamingMedia':
                raise Exception('the first tag is not SmoothStreamingMedia!')
            ism = ISM(tag)
            ism.addattrs(attrs)
            ism.generate()
            stack.append(ism)
        else:
            if ism_handlers.get(tag) is None:
                return
            child = ism_handlers[tag](tag)
            child.addattrs(attrs)
            if tag != 'ProtectionHeader':
                child.generate()
            ism.childs.append(child)
            ism = child
            stack.append(child)

    def handle_end_element(tag):
        nonlocal ism
        nonlocal ism_handlers
        if ism_handlers.get(tag) is None:
            return
        if tag == 'ProtectionHeader':
            ism.generate()
        if len(stack) > 1:
            _ = stack.pop(-1)
            ism = stack[-1]

    def handle_character_data(texts: str):
        if texts.strip() != '':
            ism.innertext += texts.strip()
    stack = []
    ism = None # type: ISM
    ism_handlers = {
        'SmoothStreamingMedia': ISM,
        'StreamIndex': StreamIndex,
        'QualityLevel': QualityLevel,
        'c': c,
        'Protection': Protection,
        'ProtectionHeader': ProtectionHeader,
    }
    parser = ParserCreate()
    parser.StartElementHandler = handle_start_element
    parser.EndElementHandler = handle_end_element
    parser.CharacterDataHandler = handle_character_data
    parser.Parse(content)
    return ism