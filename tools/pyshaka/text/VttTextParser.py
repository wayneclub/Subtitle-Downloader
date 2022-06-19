import re
from typing import Dict, List, Union
from xml.dom.minidom import parseString, Node, Element, Text
from xml.sax.saxutils import escape
from tools.pyshaka.text.Cue import Cue, defaultTextColor, fontStyle, fontWeight, textDecoration
from tools.pyshaka.log import log


class VttTextParser:

    def __init__(self):
        pass

    def parseInit(self, data: bytes):
        assert False, 'VTT does not have init segments'

    def parseMedia(self, data: bytes, time: int):
        pass

    @staticmethod
    def parseCueStyles(payload: str, rootCue: Cue, styles: Dict[str, Cue]):
        if len(styles) == 0:
            VttTextParser.addDefaultTextColor_(styles)
        # payload = VttTextParser.replaceColorPayload_(payload)
        tmp = ''
        for text in payload.split('\n'):
            if '<i>' in text and '</i>' not in text:
                tmp += text + '</i>\n'
            else:
                tmp += text + '\n'
        payload = tmp.strip()
        xmlPayload = '<span>' + escape(payload) + '</span>'
        elements = parseString(xmlPayload).getElementsByTagName(
            'span')  # type: List[Element]
        if len(elements) > 0 and elements[0]:
            element = elements[0]
            cues = []  # type: List[Cue]
            childNodes = element.childNodes  # type: List[Element]
            if len(childNodes) == 1:
                childNode = childNodes[0]
                if childNode.nodeType == Node.TEXT_NODE or childNode.nodeType == Node.CDATA_SECTION_NODE:
                    rootCue.payload = payload
                    return
            for childNode in childNodes:
                if childNode.nodeValue and childNode.nodeValue.startswith('i>'):
                    continue
                VttTextParser.generateCueFromElement_(
                    childNode, rootCue, cues, styles)
            rootCue.nestedCues = cues
        else:
            log.warning(f'The cue\'s markup could not be parsed: {payload}')
            rootCue.payload = payload

    @staticmethod
    def generateCueFromElement_(element: Union[Element, Text], rootCue: Cue, cues: List[Cue], styles: Dict[str, Cue]):
        nestedCue = rootCue.clone()
        if element.nodeType == Node.ELEMENT_NODE and element.nodeName:
            bold = fontWeight.BOLD
            italic = fontStyle.ITALIC
            underline = textDecoration.UNDERLINE
            tags = re.split('[ .]+', element.nodeName)
            for tag in tags:
                if styles.get(tag):
                    VttTextParser.mergeStyle_(nestedCue, styles.get(tag))
                if tag == 'b':
                    nestedCue.fontWeight = bold
                elif tag == 'i':
                    nestedCue.fontStyle = italic
                elif tag == 'u':
                    nestedCue.textDecoration.append(underline)
        isTextNode = element.nodeType == Node.TEXT_NODE or element.nodeType == Node.CDATA_SECTION_NODE
        if isTextNode:
            # element 这里是 Text 类型 js的textContent对应这里的data
            textArr = element.data.split('\n')
            isFirst = True
            for text in textArr:
                if not isFirst:
                    lineBreakCue = rootCue.clone()
                    lineBreakCue.lineBreak = True
                    cues.append(lineBreakCue)
                if len(text) > 0:
                    textCue = nestedCue.clone()
                    textCue.payload = text
                    cues.append(textCue)
                isFirst = False
        else:
            for childNode in element.childNodes:
                VttTextParser.generateCueFromElement_(
                    childNode, nestedCue, cues, styles)

    @staticmethod
    def replaceColorPayload_(payload: str):
        '''
        这里没有找到相关样本测试 可能有bug
        '''
        names = []
        nameStart = -1
        newPayload = ''
        for i in range(len(payload)):
            if payload[i] == '/':
                end = payload.index('>', i)
                if end <= i:
                    return payload
                tagEnd = payload[i + 1:end]
                tagStart = names.pop(-1)
                if not tagEnd or not tagStart:
                    return payload
                elif tagStart == tagEnd:
                    newPayload += '/' + tagEnd + '>'
                    i += len(tagEnd) + 1
                else:
                    if not tagStart.startsWith('c.') or tagEnd != 'c':
                        return payload
                    newPayload += '/' + tagStart + '>'
                    i += len(tagEnd) + 1
            else:
                if payload[i] == '<':
                    nameStart = i + 1
                elif payload[i] == '>':
                    if nameStart > 0:
                        names.append(payload[nameStart:i])
                        nameStart = -1
                newPayload += payload[i]
        return newPayload

    @staticmethod
    def addDefaultTextColor_(styles: Dict[str, Cue]):
        for key, value in defaultTextColor.__members__.items():
            cue = Cue(0, 0, '')
            cue.color = value
            styles[key] = cue
