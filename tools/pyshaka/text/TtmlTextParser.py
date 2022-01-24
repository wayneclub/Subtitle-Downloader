import re
from xml.dom.minidom import parseString, Element, Node, Document
from enum import Enum
from typing import List, Union

from tools.pyshaka.text.Cue import Cue, CueRegion, units, direction, writingMode
from tools.pyshaka.text.Cue import textAlign, lineAlign, positionAlign, displayAlign
from tools.pyshaka.text.Cue import fontStyle, textDecoration
from tools.pyshaka.util.TextParser import TimeContext
from tools.pyshaka.util.exceptions import InvalidXML, InvalidTextCue
from tools.pyshaka.log import log

document = Document()


class RateInfo_:
    def __init__(self, frameRate: str, subFrameRate: str, frameRateMultiplier: str, tickRate: str):
        try:
            self.frameRate = float(frameRate)
        except Exception:
            self.frameRate = 30
        try:
            self.subFrameRate = float(subFrameRate)
        except Exception:
            self.subFrameRate = 1
        try:
            self.tickRate = float(tickRate)
        except Exception:
            self.tickRate = 0
        if self.tickRate == 0:
            if frameRate:
                self.tickRate = self.frameRate * self.subFrameRate
            else:
                self.tickRate = 1
        if frameRateMultiplier:
            multiplierResults = re.findall(
                '^(\d+) (\d+)$', frameRateMultiplier)
            if len(multiplierResults) > 0:
                numerator = float(multiplierResults[1])
                denominator = float(multiplierResults[2])
                multiplierNum = numerator / denominator
                self.frameRate *= multiplierNum


class TtmlTextParser:

    def parseInit(self):
        assert False, 'TTML does not have init segments'

    def parseMedia(self, data: bytes, time: TimeContext) -> List[Cue]:
        ttpNs = parameterNs_
        ttsNs = styleNs_
        text = data.decode('utf-8')
        cues = []  # type: List[Cue]
        xml = None

        if text == '':
            return cues
        try:
            xml = parseString(text)
        except Exception as e:
            log.error('xml parseString', exc_info=e)
        if xml is None:
            return cues
        parsererrors = xml.getElementsByTagName(
            'parsererror')  # type: List[Element]
        if len(parsererrors) > 0 and parsererrors[0]:
            raise InvalidXML('ttml parsererror')
        tts = xml.getElementsByTagName('tt')  # type: List[Element]
        if len(tts) == 0:
            raise InvalidXML('TTML does not contain <tt> tag.')
        tt = tts[0]
        bodys = tt.getElementsByTagName('body')  # type: List[Element]
        if len(bodys) == 0:
            return []
        frameRate = tt.getAttributeNS(ttpNs, 'frameRate')
        subFrameRate = tt.getAttributeNS(ttpNs, 'subFrameRate')
        frameRateMultiplier = tt.getAttributeNS(ttpNs, 'frameRateMultiplier')
        tickRate = tt.getAttributeNS(ttpNs, 'tickRate')
        cellResolution = tt.getAttributeNS(ttpNs, 'cellResolution')
        spaceStyle = tt.getAttribute('xml:space') or 'default'
        extent = tt.getAttributeNS(ttsNs, 'extent')

        if spaceStyle != 'default' and spaceStyle != 'preserve':
            raise InvalidXML(f'Invalid xml:space value: {spaceStyle}')
        whitespaceTrim = spaceStyle == 'default'
        rateInfo = RateInfo_(frameRate, subFrameRate,
                             frameRateMultiplier, tickRate)
        cellResolutionInfo = TtmlTextParser.getCellResolution_(cellResolution)

        metadatas = tt.getElementsByTagName('metadata')  # type: List[Element]
        metadataElements = []
        if len(metadatas) > 0:
            for childNode in metadatas[0].childNodes:
                if isinstance(childNode, Element):
                    metadataElements.append(childNode)
        styles = tt.getElementsByTagName('style')  # type: List[Element]
        regionElements = tt.getElementsByTagName(
            'region')  # type: List[Element]
        cueRegions = []

        for region in regionElements:
            cueRegion = TtmlTextParser.parseCueRegion_(region, styles, extent)
            if cueRegion:
                cueRegions.append(cueRegion)

        body = bodys[0]
        if len([childNode for childNode in body.childNodes if isinstance(childNode, Element) and childNode.tagName == 'p']) > 0:
            raise InvalidTextCue('<p> can only be inside <div> in TTML')
        for divNode in body.childNodes:
            if isinstance(divNode, Element) is False:
                continue
            if divNode.tagName != 'div':
                continue
            has_p = False
            for pChildren in divNode.childNodes:
                if isinstance(pChildren, Element) is False:
                    continue
                if pChildren.tagName == 'span':
                    raise InvalidTextCue(
                        '<span> can only be inside <p> in TTML')
                if pChildren.tagName == 'p':
                    has_p = True
                    cue = TtmlTextParser.parseCue_(pChildren, time.periodStart, rateInfo, metadataElements,
                                                   styles, regionElements, cueRegions, whitespaceTrim, False, cellResolutionInfo)
                    if cue:
                        cues.append(cue)
            if not has_p:
                cue = TtmlTextParser.parseCue_(divNode, time.periodStart, rateInfo, metadataElements,
                                               styles, regionElements, cueRegions, whitespaceTrim, False, cellResolutionInfo)
                if cue:
                    cues.append(cue)
        return cues

    @staticmethod
    def parseCue_(cueNode: Union[Node, Element], offset, rateInfo, metadataElements, styles, regionElements, cueRegions, whitespaceTrim, isNested, cellResolution):
        cueElement = None  # type: Element
        parentElement = cueNode.parentNode  # type: Element

        if cueNode.nodeType == Node.TEXT_NODE:
            span = document.createElement('span')  # tpye: Text
            span.appendChild(cueNode)
            cueElement = span
        else:
            assert cueNode.nodeType == Node.ELEMENT_NODE, 'nodeType should be ELEMENT_NODE!'
            cueElement = cueNode
        assert cueElement, 'cueElement should be non-None!'

        spaceStyle = cueElement.getAttribute(
            'xml:space') or 'default' if whitespaceTrim else 'preserve'
        localWhitespaceTrim = spaceStyle == 'default'
        if cueElement.firstChild and cueElement.firstChild.nodeValue:
            # hasTextContent = re.match('\S', cueElement.firstChild.nodeValue)
            # \S 不匹配换行 但是js的test却会返回true
            # 所以python这里会误判 那么strip下达到修复效果
            hasTextContent = re.match(
                '\S', cueElement.firstChild.nodeValue.strip())
        else:
            hasTextContent = False
        hasTimeAttributes = cueElement.hasAttribute(
            'begin') or cueElement.hasAttribute('end') or cueElement.hasAttribute('dur')
        if not hasTimeAttributes and not hasTextContent and cueElement.tagName != 'br':
            if not isNested:
                return None
            elif localWhitespaceTrim:
                return None
        start, end = TtmlTextParser.parseTime_(cueElement, rateInfo)
        while parentElement and parentElement.nodeType == Node.ELEMENT_NODE and parentElement.tagName != 'tt':
            start, end = TtmlTextParser.resolveTime_(
                parentElement, rateInfo, start, end)
            parentElement = parentElement.parentNode
        if start is None:
            start = 0
        start += offset
        if end is None:
            end = -1
        else:
            end += offset
        if cueElement.tagName == 'br':
            cue = Cue(start, end, '')
            cue.lineBreak = True
            return cue
        payload = ''
        nestedCues = []
        flag = True
        for childNode in cueElement.childNodes:
            if childNode.nodeType != Node.TEXT_NODE:
                flag = False
                break
        if flag:
            payload: str = cueElement.firstChild.nodeValue
            if localWhitespaceTrim:
                payload = payload.strip()
                payload = re.sub('\s+', ' ', payload)
        else:
            for childNode in [_ for _ in cueElement.childNodes]:
                nestedCue = TtmlTextParser.parseCue_(
                    childNode,
                    offset,
                    rateInfo,
                    metadataElements,
                    styles,
                    regionElements,
                    cueRegions,
                    localWhitespaceTrim,
                    True,
                    cellResolution,
                )
                if nestedCue:
                    nestedCues.append(nestedCue)
        cue = Cue(start, end, payload)
        cue.nestedCues = nestedCues

        if cellResolution:
            cue.cellResolution = cellResolution

        regionElements = TtmlTextParser.getElementsFromCollection_(
            cueElement, 'region', regionElements, '')
        regionElement = None
        if len(regionElements) > 0 and regionElements[0].getAttribute('xml:id'):
            regionElement = regionElements[0]
            regionId = regionElement.getAttribute('xml:id')
            cue.region = [_ for _ in cueRegions if _.id == regionId][0]
        imageElement = None
        for nameSpace in smpteNsList_:
            imageElements = TtmlTextParser.getElementsFromCollection_(
                cueElement, 'backgroundImage', metadataElements, '#', nameSpace)
            if len(imageElements) > 0:
                imageElement = imageElements[0]
                break

        isLeaf = len(nestedCues) == 0

        TtmlTextParser.addStyle_(
            cue,
            cueElement,
            regionElement,
            imageElement,
            styles,
            isNested,
            isLeaf
        )

        return cue

    @staticmethod
    def resolveTime_(parentElement, rateInfo: RateInfo_, start, end):
        # 这里有可能存在bug
        parentTime = TtmlTextParser.parseTime_(parentElement, rateInfo)

        if start is None:
            # No start time of your own?  Inherit from the parent.
            start = parentTime[0]
        else:
            # Otherwise, the start time is relative to the parent's start time.
            if parentTime[0] is not None:
                start += parentTime[0]

        if end is None:
            # No end time of your own?  Inherit from the parent.
            end = parentTime[1]
        else:
            # Otherwise, the end time is relative to the parent's _start_ time.
            # This is not a typo.  Both times are relative to the parent's _start_.
            if parentTime[0] is not None:
                end += parentTime[0]

        return start, end

    @staticmethod
    def parseTime_(element: Element, rateInfo: RateInfo_):
        start = TtmlTextParser.parseTimeAttribute_(
            element.getAttribute('begin'), rateInfo)
        end = TtmlTextParser.parseTimeAttribute_(
            element.getAttribute('end'), rateInfo)
        duration = TtmlTextParser.parseTimeAttribute_(
            element.getAttribute('dur'), rateInfo)
        if end is None and duration is not None:
            end = start + duration
        return start, end

    @staticmethod
    def parseFramesTime_(rateInfo: RateInfo_, text):
        # 50t or 50.5t
        results = timeFramesFormat_.findall(text)
        frames = float(results[0])
        return frames / rateInfo.frameRate

    @staticmethod
    def parseTickTime_(rateInfo: RateInfo_, text):
        # 50t or 50.5t
        results = timeTickFormat_.findall(text)
        ticks = float(results[0])
        return ticks / rateInfo.tickRate

    @staticmethod
    def parseTimeFromRegex_(regex: re.Pattern, text: str) -> int:
        results = regex.findall(text)
        if len(results) == 0:
            return None
        if results[0][0] == '':
            return None

        hours = 0
        minutes = 0
        seconds = 0
        milliseconds = 0
        try:
            hours = int(results[0][0])
            minutes = int(results[0][1])
            seconds = float(results[0][2])
            milliseconds = float(results[0][3])
        except Exception:
            pass
        # 对于 timeColonFormatMilliseconds_ 来说 这里是匹配不到 milliseconds 的
        # 不过下一步计算的时候 由于seconds是小数 所以又修正了...

        return (milliseconds / 1000) + seconds + (minutes * 60) + (hours * 3600)

    @staticmethod
    def parseColonTimeWithFrames_(rateInfo: RateInfo_, text: str) -> int:
        # 01:02:43:07 ('07' is frames) or 01:02:43:07.1 (subframes)
        results = timeColonFormatFrames_.findall(text)

        hours = int(results[0][0])
        minutes = int(results[0][1])
        seconds = int(results[0][2])
        frames = int(results[0][3])
        subframes = int(results[0][4]) or 0

        frames += subframes / rateInfo.subFrameRate
        seconds += frames / rateInfo.frameRate

        return seconds + (minutes * 60) + (hours * 3600)

    @staticmethod
    def parseTimeAttribute_(text: str, rateInfo: RateInfo_):
        ret = None
        if timeColonFormatFrames_.match(text):
            ret = TtmlTextParser.parseColonTimeWithFrames_(rateInfo, text)
        elif timeColonFormat_.match(text):
            ret = TtmlTextParser.parseTimeFromRegex_(timeColonFormat_, text)
        elif timeColonFormatMilliseconds_.match(text):
            ret = TtmlTextParser.parseTimeFromRegex_(
                timeColonFormatMilliseconds_, text)
        elif timeFramesFormat_.match(text):
            ret = TtmlTextParser.parseFramesTime_(rateInfo, text)
        elif timeTickFormat_.match(text):
            ret = TtmlTextParser.parseTickTime_(rateInfo, text)
        elif timeHMSFormat_.match(text):
            ret = TtmlTextParser.parseTimeFromRegex_(timeHMSFormat_, text)
        elif text:
            raise InvalidTextCue('Could not parse cue time range in TTML')
        return ret

    @staticmethod
    def addStyle_(cue, cueElement, region, imageElement: Element, styles: List[Element], isNested: bool, isLeaf: bool):
        shouldInheritRegionStyles = isNested or isLeaf

        _direction = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'direction', shouldInheritRegionStyles)
        if _direction == 'rtl':
            cue.direction = direction.HORIZONTAL_RIGHT_TO_LEFT

        _writingMode = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'writingMode', shouldInheritRegionStyles)
        if _writingMode == 'tb' or _writingMode == 'tblr':
            cue.writingMode = writingMode.VERTICAL_LEFT_TO_RIGHT
        elif _writingMode == 'tbrl':
            cue.writingMode = writingMode.VERTICAL_RIGHT_TO_LEFT
        elif _writingMode == 'rltb' or _writingMode == 'rl':
            cue.direction = direction.HORIZONTAL_RIGHT_TO_LEFT
        elif _writingMode:
            cue.direction = direction.HORIZONTAL_LEFT_TO_RIGHT

        align = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'textAlign', shouldInheritRegionStyles)
        if align:
            cue.positionAlign = textAlignToPositionAlign_[align]
            cue.lineAlign = textAlignToLineAlign_[align]

            assert textAlign.__members__.get(
                align.upper()), f'{align.upper()} Should be in Cue.textAlign values!'
        else:
            cue.textAlign = textAlign.START

        _displayAlign = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'displayAlign', shouldInheritRegionStyles)
        if _displayAlign:
            assert displayAlign.__members__.get(_displayAlign.upper(
            )), f'{_displayAlign.upper()} Should be in Cue.displayAlign values!'
            cue.displayAlign = displayAlign[_displayAlign.upper()]

        color = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'color', shouldInheritRegionStyles)
        if color:
            cue.color = color

        backgroundColor = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'backgroundColor', shouldInheritRegionStyles)
        if backgroundColor:
            cue.backgroundColor = backgroundColor

        border = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'border', shouldInheritRegionStyles)
        if border:
            cue.border = border

        fontFamily = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'fontFamily', shouldInheritRegionStyles)
        if fontFamily:
            cue.fontFamily = fontFamily

        fontWeight = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'fontWeight', shouldInheritRegionStyles)
        if fontWeight and fontWeight == 'bold':
            cue.fontWeight = fontWeight.BOLD

        wrapOption = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'wrapOption', shouldInheritRegionStyles)
        if wrapOption and wrapOption == 'noWrap':
            cue.wrapLine = False
        else:
            cue.wrapLine = True

        lineHeight = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'lineHeight', shouldInheritRegionStyles)
        if lineHeight and unitValues_.match(lineHeight):
            cue.lineHeight = lineHeight

        fontSize = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'fontSize', shouldInheritRegionStyles)

        if fontSize:
            isValidFontSizeUnit = unitValues_.match(
                fontSize) or percentValue_.match(fontSize)
            if isValidFontSizeUnit:
                cue.fontSize = fontSize

        _fontStyle = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'fontStyle', shouldInheritRegionStyles)
        if _fontStyle:
            assert fontStyle.__members__.get(
                _fontStyle.upper()), f'{_fontStyle.upper()} Should be in Cue.fontStyle values!'
            cue.fontStyle = fontStyle[_fontStyle.upper()]

        if imageElement:
            backgroundImageType = imageElement.getAttribute(
                'imageType') or imageElement.getAttribute('imagetype')
            backgroundImageEncoding = imageElement.getAttribute('encoding')
            backgroundImageData = imageElement.textContent.trim()
            if backgroundImageType == 'PNG' and backgroundImageEncoding == 'Base64' and backgroundImageData:
                cue.backgroundImage = 'data:image/pngbase64,' + backgroundImageData

        letterSpacing = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'letterSpacing', shouldInheritRegionStyles)
        if letterSpacing and unitValues_.match(letterSpacing):
            cue.letterSpacing = letterSpacing

        linePadding = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'linePadding', shouldInheritRegionStyles)
        if linePadding and unitValues_.match(linePadding):
            cue.linePadding = linePadding

        opacity = TtmlTextParser.getStyleAttribute_(
            cueElement, region, styles, 'opacity', shouldInheritRegionStyles)
        if opacity:
            cue.opacity = float(opacity)

        textDecorationRegion = TtmlTextParser.getStyleAttributeFromRegion_(
            region, styles, 'textDecoration')
        if textDecorationRegion:
            TtmlTextParser.addTextDecoration_(cue, textDecorationRegion)

        textDecorationElement = TtmlTextParser.getStyleAttributeFromElement_(
            cueElement, styles, 'textDecoration')
        if textDecorationElement:
            TtmlTextParser.addTextDecoration_(cue, textDecorationElement)

    @staticmethod
    def addTextDecoration_(cue: Cue, decoration):
        # 这里可能有问题 .value
        for value in decoration.split(' '):
            if value == 'underline':
                if textDecoration.UNDERLINE not in cue.textDecoration:
                    cue.textDecoration.append(textDecoration.UNDERLINE)
            elif value == 'noUnderline':
                cue.textDecoration = [
                    _ for _ in cue.textDecoration if textDecoration.UNDERLINE != _]
            elif value == 'lineThrough':
                if textDecoration.LINE_THROUGH not in cue.textDecoration:
                    cue.textDecoration.append(textDecoration.LINE_THROUGH)
            elif value == 'noLineThrough':
                cue.textDecoration = [
                    _ for _ in cue.textDecoration if textDecoration.LINE_THROUGH != _]
            elif value == 'overline':
                if textDecoration.OVERLINE not in cue.textDecoration:
                    cue.textDecoration.append(textDecoration.OVERLINE)
            elif value == 'noOverline':
                cue.textDecoration = [
                    _ for _ in cue.textDecoration if textDecoration.OVERLINE != _]

    @staticmethod
    def getStyleAttribute_(cueElement, region, styles, attribute, shouldInheritRegionStyles=True):
        attr = TtmlTextParser.getStyleAttributeFromElement_(
            cueElement, styles, attribute)
        if attr:
            return attr
        if shouldInheritRegionStyles:
            return TtmlTextParser.getStyleAttributeFromRegion_(region, styles, attribute)
        return None

    @staticmethod
    def parseCueRegion_(regionElement: Element, styles: List[Element], globalExtent: str):
        region = CueRegion()
        _id = regionElement.getAttribute('xml:id')
        if not _id:
            log.warning(
                'TtmlTextParser parser encountered a region with no id. Region will be ignored.')
            return None
        region.id = _id
        globalResults = None
        if globalExtent:
            globalResults = percentValues_.findall(
                globalExtent) or pixelValues_.findall(globalExtent)
        if globalResults is not None and len(globalResults) == 2:
            globalWidth = int(globalResults[0][0])
            globalHeight = int(globalResults[0][1])
        else:
            globalWidth = None
            globalHeight = None
        results = None
        percentage = None

        extent = TtmlTextParser.getStyleAttributeFromRegion_(
            regionElement, styles, 'extent')
        if extent:
            percentage = percentValues_.findall(extent)
            results = percentage or pixelValues_.findall(extent)
            if results is not None:
                region.width = int(results[0][0])
                region.height = int(results[0][1])

                if not percentage:
                    if globalWidth is not None:
                        region.width = region.width * 100 / globalWidth
                    if globalHeight is not None:
                        region.height = region.height * 100 / globalHeight
                if percentage or globalWidth is not None:
                    region.widthUnits = units.PERCENTAGE
                else:
                    region.widthUnits = units.PX
                if percentage or globalHeight is not None:
                    region.heightUnits = units.PERCENTAGE
                else:
                    region.heightUnits = units.PX
        origin = TtmlTextParser.getStyleAttributeFromRegion_(
            regionElement, styles, 'origin')
        if origin:
            percentage = percentValues_.findall(origin)
            results = percentage or pixelValues_.findall(origin)
            if len(results) > 0:
                region.viewportAnchorX = int(results[0][0])
                region.viewportAnchorY = int(results[0][1])
            if len(percentage) == 0:
                if globalHeight is not None:
                    region.viewportAnchorY = region.viewportAnchorY * 100 / globalHeight
                if globalWidth is not None:
                    region.viewportAnchorX = region.viewportAnchorX * 100 / globalHeight
            if percentage or globalWidth is not None:
                region.viewportAnchorUnits = units.PERCENTAGE
            else:
                region.viewportAnchorUnits = units.PX
        return region

    @staticmethod
    def getInheritedStyleAttribute_(element: Element, styles, attribute):
        ttsNs = styleNs_
        ebuttsNs = styleEbuttsNs_

        inheritedStyles = TtmlTextParser.getElementsFromCollection_(
            element, 'style', styles, '')  # tpye: List[Element]

        styleValue = None
        # The last value in our styles stack takes the precedence over the others
        for inheritedStyle in inheritedStyles:
            # Check ebu namespace first.
            styleAttributeValue = inheritedStyle.getAttributeNS(
                ebuttsNs, attribute)

            if not styleAttributeValue:
                # Fall back to tts namespace.
                styleAttributeValue = inheritedStyle.getAttributeNS(
                    ttsNs, attribute)

            if not styleAttributeValue:
                # Next, check inheritance.
                # Styles can inherit from other styles, so traverse up that chain.
                styleAttributeValue = TtmlTextParser.getStyleAttributeFromElement_(
                    inheritedStyle, styles, attribute)

            if styleAttributeValue:
                styleValue = styleAttributeValue

        return styleValue

    @staticmethod
    def getStyleAttributeFromElement_(cueElement: Element, styles, attribute: str):
        ttsNs = styleNs_
        elementAttribute = cueElement.getAttributeNS(ttsNs, attribute)
        if elementAttribute:
            return elementAttribute
        return TtmlTextParser.getInheritedStyleAttribute_(cueElement, styles, attribute)

    @staticmethod
    def getInheritedAttribute_(element: Element, attributeName: str, nsName: str):
        ret = None
        while element:
            if nsName:
                ret = element.getAttributeNS(nsName, attributeName)
            else:
                ret = element.getAttribute(attributeName)
            if ret:
                break
            parentNode = element.parentNode
            if isinstance(parentNode, Element):
                element = parentNode
            else:
                break
        return ret

    @staticmethod
    def getElementsFromCollection_(element: Element, attributeName: str, collection: list, prefixName: str, nsName: str = None):
        items = []
        if not element or len(collection) < 1:
            return items
        attributeValue = TtmlTextParser.getInheritedAttribute_(
            element, attributeName, nsName)
        if not attributeValue:
            return items
        itemNames = attributeValue.split(' ')
        for name in itemNames:
            for item in collection:
                if prefixName + item.getAttribute('xml:id') == name:
                    items.append(item)
                    break
        return items

    @staticmethod
    def getStyleAttributeFromRegion_(region: Element, styles, attribute):
        ttsNs = styleNs_
        if not region:
            return None
        attr = region.getAttributeNS(ttsNs, attribute)
        if attr:
            return attr
        return TtmlTextParser.getInheritedStyleAttribute_(region, styles, attribute)

    @staticmethod
    def getCellResolution_(cellResolution: str):
        if cellResolution is None or cellResolution == '':
            return None
        matches = re.findall('^(\d+) (\d+)$', cellResolution)
        if len(matches) == 0:
            return None
        columns = int(matches[0][0])
        rows = int(matches[0][1])
        return {'columns': columns, 'rows': rows}


# 50.17% 10%
percentValues_ = re.compile(
    '^(\d{1,2}(?:\.\d+)?|100(?:\.0+)?)% (\d{1,2}(?:\.\d+)?|100(?:\.0+)?)%$')

# 0.6% 90%
percentValue_ = re.compile('^(\d{1,2}(?:\.\d+)?|100)%$')

# 100px, 8em, 0.80c
unitValues_ = re.compile('^(\d+px|\d+em|\d*\.?\d+c)$')

# 100px
pixelValues_ = re.compile('^(\d+)px (\d+)px$')

# 00:00:40:07 (7 frames) or 00:00:40:07.1 (7 frames, 1 subframe)
timeColonFormatFrames_ = re.compile(
    '^(\d{2,}):(\d{2}):(\d{2}):(\d{2})\.?(\d+)?$')

# 00:00:40 or 00:40
timeColonFormat_ = re.compile('^(?:(\d{2,}):)?(\d{2}):(\d{2})$')

# 01:02:43.0345555 or 02:43.03
timeColonFormatMilliseconds_ = re.compile(
    '^(?:(\d{2,}):)?(\d{2}):(\d{2}\.\d{2,})$')

# 75f or 75.5f
timeFramesFormat_ = re.compile('^(\d*(?:\.\d*)?)f$')

# 50t or 50.5t
timeTickFormat_ = re.compile('^(\d*(?:\.\d*)?)t$')

# 3.45h, 3m or 4.20s
timeHMSFormat_ = re.compile(
    '^(?:(\d*(?:\.\d*)?)h)?(?:(\d*(?:\.\d*)?)m)?(?:(\d*(?:\.\d*)?)s)?(?:(\d*(?:\.\d*)?)ms)?$')


class textAlignToLineAlign_(Enum):
    left = lineAlign.START
    center = lineAlign.CENTER
    right = lineAlign.END
    start = lineAlign.START
    end = lineAlign.END


class textAlignToPositionAlign_(Enum):
    left = positionAlign.LEFT
    center = positionAlign.CENTER
    right = positionAlign.RIGHT


parameterNs_ = 'http://www.w3.org/ns/ttml#parameter'
styleNs_ = 'http://www.w3.org/ns/ttml#styling'
styleEbuttsNs_ = 'urn:ebu:tt:style'
smpteNsList_ = [
    'http://www.smpte-ra.org/schemas/2052-1/2010/smpte-tt',
    'http://www.smpte-ra.org/schemas/2052-1/2013/smpte-tt',
]
