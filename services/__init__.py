#!/usr/bin/python3
# coding: utf-8

"""
This module is for service initiation mapping
"""

from constants import Service
from services.kktv import KKTV
from services.linetv import LineTV
from services.fridayvideo import FridayVideo
from services.catchplay import CatchPlay
from services.iqiyi.iqiyi import IQIYI
from services.mewatch import MeWatch
from services.myvideo import MyVideo
from services.nowplayer import NowPlayer
from services.wetv.wetv import WeTV
from services.viki import Viki
from services.viu import Viu
from services.nowe import NowE
from services.disneyplus.disneyplus import DisneyPlus
from services.hbogoasia import HBOGOAsia
from services.itunes import iTunes
from services.appletvplus import AppleTVPlus
from services.youtube import YouTube

service_map = [
    {
        'name': Service.APPLETVPLUS,
        'class': AppleTVPlus,
        'keyword': 'tv.apple.com',
    },
    {
        'name': Service.CATCHPLAY,
        'class': CatchPlay,
        'keyword': 'catchplay.com'
    },
    {
        'name': Service.DISNEYPLUS,
        'class': DisneyPlus,
        'keyword': 'disneyplus.com'
    },
    {
        'name': Service.FRIDAYVIDEO,
        'class': FridayVideo,
        'keyword': 'video.friday.tw'
    },
    {
        'name': Service.HBOGOASIA,
        'class': HBOGOAsia,
        'keyword': 'hbogoasia'
    },
    {
        'name': Service.IQIYI,
        'class': IQIYI,
        'keyword': 'iq.com'
    },
    {
        'name': Service.ITUNES,
        'class': iTunes,
        'keyword': 'itunes.apple.com',
    },
    {
        'name': Service.KKTV,
        'class': KKTV,
        'keyword': 'kktv.me'
    },
    {
        'name': Service.LINETV,
        'class': LineTV,
        'keyword': 'linetv.tw'
    },
    {
        'name': Service.MEWATCH,
        'class': MeWatch,
        'keyword': 'mewatch.sg'
    },
    {
        'name': Service.MYVIDEO,
        'class': MyVideo,
        'keyword': 'myvideo.net.tw'
    },
    {
        'name': Service.NOWE,
        'class': NowE,
        'keyword': 'nowe.com'
    },
    {
        'name': Service.NOWPLAYER,
        'class': NowPlayer,
        'keyword': 'nowplayer.now.com'
    },
    {
        'name': Service.VIKI,
        'class': Viki,
        'keyword': 'viki.com'
    },
    {
        'name': Service.VIU,
        'class': Viu,
        'keyword': 'viu.com'
    },
    {
        'name': Service.WETV,
        'class': WeTV,
        'keyword': 'wetv.vip'
    },
    {
        'name': Service.YOUTUBE,
        'class': YouTube,
        'keyword': 'youtube.com'
    }
]
