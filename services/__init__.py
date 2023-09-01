
from configs.config import Platform
from services.kktv import KKTV
from services.linetv import LineTV
from services.fridayvideo import FridayVideo
from services.catchplay import CatchPlay
from services.iqiyi.iqiyi import IQIYI
from services.myvideo import MyVideo
from services.nowplayer import NowPlayer
from services.wetv.wetv import WeTV
from services.viu import Viu
from services.nowe import NowE
from services.disneyplus.disneyplus import DisneyPlus
from services.hbogoasia import HBOGOAsia
from services.itunes import iTunes
from services.appletvplus import AppleTVPlus

service_map = [
    {
        'name': Platform.APPLETVPLUS,
        'class': AppleTVPlus,
        'keyword': 'tv.apple.com',
    },
    {
        'name': Platform.CATCHPLAY,
        'class': CatchPlay,
        'keyword': 'catchplay.com'
    },
    {
        'name': Platform.DISNEYPLUS,
        'class': DisneyPlus,
        'keyword': 'disneyplus.com'
    },
    {
        'name': Platform.FRIDAYVIDEO,
        'class': FridayVideo,
        'keyword': 'video.friday.tw'
    },
    {
        'name': Platform.HBOGOASIA,
        'class': HBOGOAsia,
        'keyword': 'hbogoasia'
    },
    {
        'name': Platform.IQIYI,
        'class': IQIYI,
        'keyword': 'iq.com'
    },
    {
        'name': Platform.ITUNES,
        'class': iTunes,
        'keyword': 'itunes.apple.com',
    },
    {
        'name': Platform.KKTV,
        'class': KKTV,
        'keyword': 'kktv.me'
    },
    {
        'name': Platform.LINETV,
        'class': LineTV,
        'keyword': 'linetv.tw'
    },
    {
        'name': Platform.MYVIDEO,
        'class': MyVideo,
        'keyword': 'myvideo.net.tw'
    },
    {
        'name': Platform.NOWE,
        'class': NowE,
        'keyword': 'nowe.com'
    },
    {
        'name': Platform.NOWPLAYER,
        'class': NowPlayer,
        'keyword': 'nowplayer.now.com'
    },
    {
        'name': Platform.VIU,
        'class': Viu,
        'keyword': 'viu.com'
    },
    {
        'name': Platform.WETV,
        'class': WeTV,
        'keyword': 'wetv.vip'
    }
]
