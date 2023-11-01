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
from services.crunchyroll import Crunchyroll
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
        'domain': 'tv.apple.com',
    },
    {
        'name': Service.CATCHPLAY,
        'class': CatchPlay,
        'domain': 'catchplay.com'
    },
    {
        'name': Service.CRUNCHYROLL,
        'class': Crunchyroll,
        'domain': 'crunchyroll.com'
    },
    {
        'name': Service.DISNEYPLUS,
        'class': DisneyPlus,
        'domain': 'disneyplus.com'
    },
    {
        'name': Service.FRIDAYVIDEO,
        'class': FridayVideo,
        'domain': 'video.friday.tw'
    },
    {
        'name': Service.HBOGOASIA,
        'class': HBOGOAsia,
        'domain': 'hbogoasia'
    },
    {
        'name': Service.IQIYI,
        'class': IQIYI,
        'domain': 'iq.com'
    },
    {
        'name': Service.ITUNES,
        'class': iTunes,
        'domain': 'itunes.apple.com',
    },
    {
        'name': Service.KKTV,
        'class': KKTV,
        'domain': 'kktv.me'
    },
    {
        'name': Service.LINETV,
        'class': LineTV,
        'domain': 'linetv.tw'
    },
    {
        'name': Service.MEWATCH,
        'class': MeWatch,
        'domain': 'mewatch.sg'
    },
    {
        'name': Service.MYVIDEO,
        'class': MyVideo,
        'domain': 'myvideo.net.tw'
    },
    {
        'name': Service.NOWE,
        'class': NowE,
        'domain': 'nowe.com'
    },
    {
        'name': Service.NOWPLAYER,
        'class': NowPlayer,
        'domain': 'nowplayer.now.com'
    },
    {
        'name': Service.VIKI,
        'class': Viki,
        'domain': 'viki.com'
    },
    {
        'name': Service.VIU,
        'class': Viu,
        'domain': 'viu.com'
    },
    {
        'name': Service.WETV,
        'class': WeTV,
        'domain': 'wetv.vip'
    },
    {
        'name': Service.YOUTUBE,
        'class': YouTube,
        'domain': 'youtube.com'
    }
]
