#!/usr/bin/python3
# coding: utf-8

"""
This module is for constants
"""


class Service:
    """
    Define all streaming services name
    """

    APPLETVPLUS = 'AppleTVPlus'
    CATCHPLAY = 'CatchPlay'
    DISNEYPLUS = 'DisneyPlus'
    FRIDAYVIDEO = 'FridayVideo'
    HBOGOASIA = 'HBOGOAsia'
    IQIYI = 'iQIYI'
    ITUNES = 'iTunes'
    KKTV = 'KKTV'
    LINETV = 'LineTV'
    MEWATCH = 'meWATCH'
    MYVIDEO = 'MyVideo'
    NOWE = 'NowE'
    NOWPLAYER = 'NowPlayer'
    VIKI = 'Viki'
    VIU = 'Viu'
    WETV = 'WeTV'
    YOUTUBE = 'YouTube'


SUBTITLE_FORMAT = ['.srt', '.ass', '.ssa', '.vtt', '.xml']

ISO_6391 = {
    'cht': 'zh-Hant',
    'tw': 'zh-Hant',
    'zh-hant': 'zh-Hant',
    'zh-tw': 'zh-Hant',
    'zho': 'zh-Hant',
    'cmn-hant': 'zh-Hant',
    'zh-hk': 'zh-HK',
    'hk': 'zh-HK',
    'hkg': 'zh-HK',
    'cmn-hk': 'zh-HK',
    'zh-hans': 'zh-Hans',
    'cmn-hans': 'zh-Hans',
    'chs': 'zh-Hans',
    'cn': 'zh-Hans',
    'chn': 'zh-Hant',
    'chc': 'zh-Hant',
    'chz': 'zh-Hans',
    'zh-cn': 'zh-Hans',
    'zh': 'zh-Hans',
    'us': 'en',
    'gb': 'en',
    'gbr': 'en',
    'kor': 'ko',
    'kr': 'ko',
    'ko-kr': 'ko',
    'ko-ko': 'ko',
    'jpn': 'ja',
    'jp': 'ja',
    'ja-jp': 'ja',
    'rus': 'ru',
    'msa': 'ms',
    'mya': 'my',
    'tha': 'th',
    'ind': 'id',
    'id-id': 'id',
    'vie': 'vi',
    'ara': 'ar',
    'spa': 'es',
    'deu': 'de',
    'fra': 'fr',
    'nor': 'no',
    'por': 'pt',
    '英語': 'en',
    '繁體中文': 'zh-Hant',
    '簡體中文': 'zh-Hans',
    '韓語': 'ko',
    '馬來語': 'ms',
    '越南語': 'vi',
    '泰語': 'th',
    '印尼語': 'id',
    '阿拉伯語': 'ar',
    '西班牙語': 'es',
    '葡萄牙語': 'pt',
    '日語': 'ja',
    'traditional chinese': 'zh-Hant',
    'simplified chinese':  'zh-Hans',
    'bahasa malaysia': 'ms',
    'thai': 'th',
    'vietnamese': 'vi',
    'bahasa indonesia': 'id',
    'indonesian': 'id',
    'english': 'en',
    'korean': 'ko',
    'arabic': 'ar',
    'spanish': 'es',
    'portuguese': 'pt',
    'japanese': 'ja'
}

LANGUAGE_LIST = [
    ["Hindi", "hin", "hin", "Hindi"],
    ["Tamil", "tam", "tam", "Tamil"],
    ["Telugu", "tel", "tel", "Telugu"],
    ["English", "eng", "eng", "English"],
    ["Afrikaans", "af", "afr", "Afrikaans"],
    ["Arabic", "ara", "ara", "Arabic"],
    ["Arabic (Syria)", "araSy", "ara", "Arabic Syria"],
    ["Arabic (Egypt)", "araEG", "ara", "Arabic Egypt"],
    ["Arabic (Kuwait)", "araKW", "ara", "Arabic Kuwait"],
    ["Arabic (Lebanon)", "araLB", "ara", "Arabic Lebanon"],
    ["Arabic (Algeria)", "araDZ", "ara", "Arabic Algeria"],
    ["Arabic (Bahrain)", "araBH", "ara", "Arabic Bahrain"],
    ["Arabic (Iraq)", "araIQ", "ara", "Arabic Iraq"],
    ["Arabic (Jordan)", "araJO", "ara", "Arabic Jordan"],
    ["Arabic (Libya)", "araLY", "ara", "Arabic Libya"],
    ["Arabic (Morocco)", "araMA", "ara", "Arabic Morocco"],
    ["Arabic (Oman)", "araOM", "ara", "Arabic Oman"],
    ["Arabic (Saudi Arabia)", "araSA",
     "ara", "Arabic Saudi Arabia"],
    ["Arabic (Tunisia)", "araTN", "ara", "Arabic Tunisia"],
    [
        "Arabic (United Arab Emirates)",
        "araAE",
        "ara",
        "Arabic United Arab Emirates",
    ],
    ["Arabic (Yemen)", "araYE", "ara", "Arabic Yemen"],
    ["Armenian", "hye", "arm", "Armenian"],
    ["Assamese", "asm", "asm", "Assamese"],
    ["Bengali", "ben", "ben", "Bengali"],
    ["Basque", "eus", "baq", "Basque"],
    ["British English", "enGB", "eng", "British English"],
    ["Bulgarian", "bul", "bul", "Bulgarian"],
    ["Cantonese", "None", "chi", "Cantonese"],
    ["Catalan", "cat", "cat", "Catalan"],
    ["Simplified Chinese", "zhoS", "chi", "Simplified Chinese"],
    ["Traditional Chinese", "zhoT", "chi", "Traditional Chinese"],
    ["Croatian", "hrv", "hrv", "Croatian"],
    ["Czech", "ces", "cze", "Czech"],
    ["Danish", "dan", "dan", "Danish"],
    ["Dutch", "nld", "dut", "Dutch"],
    ["Estonian", "est", "est", "Estonian"],
    ["Filipino", "fil", "fil", "Filipino"],
    ["Finnish", "fin", "fin", "Finnish"],
    ["Flemish", "nlBE", "dut", "Flemish"],
    ["French", "fra", "fre", "French"],
    ["French Canadian", "caFra", "fre", "French Canadian"],
    ["Canadian French", "caFra", "fre", "Canadian French"],
    ["German", "deu", "ger", "German"],
    ["Greek", "ell", "gre", "Greek"],
    ["Gujarati", "guj", "guj", "Gujarati"],
    ["Hebrew", "heb", "heb", "Hebrew"],
    ["Hungarian", "hun", "hun", "Hungarian"],
    ["Icelandic", "isl", "ice", "Icelandic"],
    ["Indonesian", "ind", "ind", "Indonesian"],
    ["Italian", "ita", "ita", "Italian"],
    ["Japanese", "jpn", "jpn", "Japanese"],
    ["Kannada (India)", "kan", "kan", "Kannada (India)"],
    ["Khmer", "khm", "khm", "Khmer"],
    ["Klingon", "tlh", "tlh", "Klingon"],
    ["Korean", "kor", "kor", "Korean"],
    ["Lithuanian", "lit", "lit", "Lithuanian"],
    ["Latvian", "lav", "lav", "Latvian"],
    ["Malay", "msa", "may", "Malay"],
    ["Malayalam", "mal", "mal", "Malayalam"],
    ["Mandarin", "None", "chi", "Mandarin"],
    ["Mandarin (Putonghua)", "zho", "chi", "Mandarin (Putonghua)"],
    ["Mandarin Chinese (Simplified)", "zh-Hans", "chi", "Simplified Chinese"],
    ["Mandarin Chinese (Traditional)", "zh-Hant",
     "chi", "Traditional Chinese"],
    ["Traditional Chinese", "mul", "chi", "Multiple Language"],
    ["Mandarin Chinese", "zh", "chi", "Mandarin Chinese"],
    ["Yue Chinese", "yue", "chi", "(Yue Chinese)"],
    ["Manipuri", "mni", "mni", "Manipuri"],
    ["Marathi", "mar", "mar", "Marathi"],
    ["No Dialogue", "zxx", "zxx", "No Dialogue"],
    ["Norwegian", "nor", "nor", "Norwegian"],
    ["Norwegian Bokmal", "nob", "nob", "Norwegian Bokmal"],
    ["Persian", "fas", "per", "Persian"],
    ["Polish", "pol", "pol", "Polish"],
    ["Portuguese", "por", "por", "Portuguese"],
    ["Brazilian Portuguese", "brPor", "por", "Brazilian Portuguese"],
    ["Punjabi", "pan", "pan", "Punjabi"],
    ["Panjabi", "pan", "pan", "Panjabi"],
    ["Romanian", "ron", "rum", "Romanian"],
    ["Russian", "rus", "rus", "Russian"],
    ["Serbian", "srp", "srp", "Serbian"],
    ["Sinhala", "sin", "sin", "Sinhala"],
    ["Slovak", "slk", "slo", "Slovak"],
    ["Slovenian", "slv", "slv", "Slovenian"],
    ["Spanish", "spa", "spa", "Spanish"],
    ["European Spanish", "euSpa", "spa", "European Spanish"],
    ["Swedish", "swe", "swe", "Swedish"],
    ["Thai", "tha", "tha", "Thai"],
    ["Tagalog", "tgl", "tgl", "Tagalog"],
    ["Turkish", "tur", "tur", "Turkish"],
    ["Ukrainian", "ukr", "ukr", "Ukrainian"],
    ["Urdu", "urd", "urd", "Urdu"],
    ["Vietnamese", "vie", "vie", "Vietnamese"],
]
