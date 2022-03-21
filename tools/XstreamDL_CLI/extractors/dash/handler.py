from xml.parsers.expat import ParserCreate
from .mpd import MPD
from .childs.location import Location
from .childs.adaptationset import AdaptationSet
from .childs.baseurl import BaseURL
from .childs.cencpssh import CencPssh
from .childs.contentprotection import ContentProtection
from .childs.period import Period
from .childs.representation import Representation
from .childs.role import Role
from .childs.s import S
from .childs.segmentlist import SegmentList
from .childs.initialization import Initialization
from .childs.segmenturl import SegmentURL
from .childs.segmentbase import SegmentBaee
from .childs.segmenttemplate import SegmentTemplate
from .childs.segmenttimeline import SegmentTimeline


def xml_handler(content: str):
    def handle_start_element(tag, attrs):
        nonlocal mpd
        nonlocal mpd_handlers
        if mpd is None:
            if tag != 'MPD':
                raise Exception('the first tag is not MPD!')
            mpd = MPD(tag)
            mpd.addattrs(attrs)
            mpd.generate()
            stack.append(mpd)
        else:
            if mpd_handlers.get(tag) is None:
                return
            child = mpd_handlers[tag](tag)
            child.addattrs(attrs)
            child.generate()
            mpd.childs.append(child)
            mpd = child
            stack.append(child)

    def handle_end_element(tag):
        nonlocal mpd
        nonlocal mpd_handlers
        if mpd_handlers.get(tag) is None:
            return
        if len(stack) > 1:
            _ = stack.pop(-1)
            mpd = stack[-1]

    def handle_character_data(texts: str):
        if texts.strip() != '':
            mpd.innertext += texts.strip()
    stack = []
    mpd = None # type: MPD
    mpd_handlers = {
        'MPD': MPD,
        'Location': Location,
        'BaseURL': BaseURL,
        'Period': Period,
        'AdaptationSet': AdaptationSet,
        'Representation': Representation,
        'SegmentTemplate': SegmentTemplate,
        'SegmentURL': SegmentURL,
        'SegmentBase': SegmentBaee,
        'Initialization': Initialization,
        'SegmentList': SegmentList,
        'SegmentTimeline': SegmentTimeline,
        'Role': Role,
        'S': S,
        'ContentProtection': ContentProtection,
        'cenc:pssh': CencPssh,
    }
    parser = ParserCreate()
    parser.StartElementHandler = handle_start_element
    parser.EndElementHandler = handle_end_element
    parser.CharacterDataHandler = handle_character_data
    parser.Parse(content)
    return mpd