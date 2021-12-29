# Subtitle-Downloader



<a href="https://colab.research.google.com/drive/13tv-eT5mx6EWBL_du9Bd2gMQFxT83NCp?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a> <br/>

Subtitle-Downloader supports downloading subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iQIYI.

## DESCRIPTION

Subtitle-Downloader is a command-line program to download subtitles from most popular streaming platform especially for Traditional Chinese users. It requires the Python interpreter, version 3.6+, and it is not platform specific. It should work on your Unix box, on Windows or on macOS. It is released to the public domain, which means you can modify it, redistribute it or use it; however this is only for personal research.

## INSTALLATION

```
pip install -r requriements
```

## USAGE

```
python download_subtitle.py URL [OPTIONS]
```

## OPTIONS

```
  -h, --help                  show this help message and exit
  -s --season                 download season [0-9]
  -l, --last-episode          download last episode
  -o, --output                output directory
  -email, --email             account for Disney Plus and HBOGO Asia
  -password, --password       password for Disney Plus and HBOGO Asia
  -slang, --subtitle-language subtitle-language for Disney Plus and HBOGO Asia
  -alang, --audio-language    audio-language for Disney Plus
```

目前只支持從
1. KKTV 下載電影、劇集、綜藝、動漫字幕
2. LineTV 下載劇集、綜藝字幕
3. FriDay影音 下載劇集、電影、綜藝、動漫字幕
4. 愛奇藝 下載劇集
4. Disney+ 下載電影、劇集
5. HBOGO Asia 下載電影、劇集

請確認網站網址無誤

使用方式：
![alt text](https://github.com/wayneclub/Subtitle-Downloader/blob/main/guide.png?raw=true)
