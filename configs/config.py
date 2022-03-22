#!/usr/bin/python3
# coding: utf-8

"""
This module is for config.
"""
from os.path import dirname

script_name = "Subtitle Downloader"
__version__ = "1.0.0"


dir_path = dirname(dirname(__file__)).replace("\\", "/")

PATHS = {
    "cookies":  f"{dir_path}/configs/cookies",
    "downloads": f"{dir_path}/downloads",
    "logs": f"{dir_path}/logs",
}


class Platform:

    KKTV = "KKTV"
    LINETV = "LineTV"
    FRIDAY = "friDay"
    CATCHPLAY = 'CatchPlay'
    IQIYI = "iQIYI"
    WETV = 'WeTV'
    VIU = "Viu"
    NOWE = 'NowE'
    NETFLIX = "Netflix"
    DISNEYPLUS = "Disney+"
    HBOGO = "HBOGO"
    APPLETV = 'AppleTV'
    ITUNES = "iTunes"


CREDENTIAL = {}

CREDENTIAL[Platform.CATCHPLAY] = {
    "cookies_file": f"{PATHS['cookies']}/cookies_catchplay.txt",
    "cookies_txt": f"{PATHS['cookies']}/catchplay.com_cookies.txt"
}

CREDENTIAL[Platform.DISNEYPLUS] = {
    # Enter the email address of your Disney Plus account here
    "email": "",
    # Enter the password of your Disney Plus account here
    "password": "",
}

CREDENTIAL[Platform.HBOGO] = {
    # Enter the username of your HBOGO account here
    "username": "",
    # Enter the password of your HBOGO account here
    "password": "",
}

CREDENTIAL[Platform.NOWE] = {
    "cookies_file": f"{PATHS['cookies']}/cookies_nowe.txt",
    "cookies_txt": f"{PATHS['cookies']}/nowe.com_cookies.txt",
    # Copy user-agent from login browser (https://www.whatsmyua.info/)
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
}

VPN = {
    "proxies": (
        "http://127.0.0.1:7890",
    ),
    "nordvpn": {
        "port": "80",
        # Advanced configuration (https://my.nordaccount.com/dashboard/nordvpn/)
        "username": "",
        "password": "",
        "http": "http://{email}:{passwd}@{ip}:{port}",
    },
    "private": {
        "port": "8080",
        # Enter the email address of your VPN account here
        "email": "enter your email address here",
        # Enter the password of your VPN account here
                "passwd": "enter your password here",
                "http": "http://{email}:{passwd}@{ip}:{port}",
    },
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"

ISO_6391 = {
    'cht': 'zh-Hant',
    'tw': 'zh-Hant',
    'zh-tw': 'zh-Hant',
    'hk': 'Cantonese',
    'hkg': 'Cantonese',
    'chs': 'zh-Hans',
    'cn': 'zh-Hans',
    'chn': 'zh-Hans',
    'zh-cn': 'zh-Hans',
    'us': 'eng',
    'gb': 'eng',
    'gbr': 'eng',
    'en': 'eng',
    'en-us': 'eng',
    'en-gb': 'eng',
    'en-ca': 'eng',
    'ko': 'kor',
    'kr': 'kor',
    'ko_kr': 'kor',
    'ko-kr': 'kor',
    'ko-ko': 'kor',
    'ja': 'jpn',
    'jp': 'jpn',
    'jpg': 'jpn',
    'ja-jp': 'jpn',
    'ru': 'rus',
    'ms': 'msa',
    'th': 'tha',
    'id': 'ind',
    'vi': 'vie',
    'ar': 'ara',
    'es': 'spa',
    'de': 'deu',
    'fr': 'fra',
    'no': 'nor',
    'pt': 'por'
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


class Config:

    def credential(self, name):
        return CREDENTIAL[name]

    def paths(self):
        return PATHS

    def language_list(self):
        return LANGUAGE_LIST

    def get_language_code(self, lang):
        if ISO_6391.get(lang.lower()):
            return ISO_6391.get(lang.lower())
        else:
            return lang

    def vpn(self):
        return VPN

    def get_platforms(self):
        streaming_service = Platform()
        return [attr.lower() for attr in dir(streaming_service) if not callable(
            getattr(streaming_service, attr)) and not attr.startswith("__")]

    def get_user_agent(self):
        return USER_AGENT
