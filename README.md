# Subtitle-Downloader

**NON-COMMERCIAL USE ONLY**

<a href="https://colab.research.google.com/drive/13tv-eT5mx6EWBL_du9Bd2gMQFxT83NCp?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a> <br/>

Subtitle-Downloader supports downloading subtitles from Disney Plus, HBOGO Asia, KKTV, LineTV, friDay Video, iq.com.

## DESCRIPTION

Subtitle-Downloader is a command-line program to download subtitles from the most popular streaming platform. It requires the Python interpreter, version 3.6+, and is not platform specific. It should work on your Unix box, on Windows or on macOS. This project is only for personal research and language learning.

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
  -h, --help                    show this help message and exit
  
  -s --season                   download season [0-9]
  
  -l, --last-episode            download last episode
  
  -o, --output                  output directory
  
  -email, --email               account for Disney Plus and HBOGO Asia
  
  -password, --password         password for Disney Plus and HBOGO Asia
  
  -slang, --subtitle-language   Languages of HBOGO Asia's and Disney Plus's subtitles to download (optional) separated by commas
                                default: Traditional Chinese
                                all: download all available languages
                                
  -alang, --audio-language      Languages of Disney Plus's audio-tracks to download (optional) separated by commas
```
## Subtitle Languages

iq.com

| Codec | Language | 語言 |
| --- | --- | --- |
| en | English | 英文 |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese | 簡體中文 |
| ms | Malay | 馬來文 |
| vi | Vietnamese | 越南文 |
| th | Thai | 泰文 |
| id | Indonesian | 印尼文 |
| ar | Arabic | 阿拉伯文 |

HBOGO Asia

| Codec | Language | 語言 |
| --- | --- | --- |
| en | English | 英文 |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese | 簡體中文 |
| ms | Malay | 馬來文 |
| th | Thai | 泰文 |
| id | Indonesian | 印尼文 |

Disney Plus

| Codec | Language | 語言 |
| --- | --- | --- |
| en | English [CC] | 英文 |
| zh-Hant | Chinese (Traditional) | 台繁 |
| zh-Hans | Chinese (Simplified) | 簡中 |
| zh-HK | Cantonese | 港繁 |
| da | Dansk | 丹麥文 |
| de | Deutsch | 德文 |
| es-ES | Español | 西班牙文 |
| es-419 | Español (Latinoamericano) | 西班牙文（拉丁美洲 |
| fr-FR | Français | 法文 |
| fr-CA | Français (Canadien) | 法文（加拿大） |
| it | Italiano | 義大利文 |
| ja | Japanese | 日文 |
| ko | Korean | 韓文 |
| nl | Nederlands | 荷蘭文 |
| no | Norsk | 挪威文 |
| pt-PT | Português | 葡萄牙文 |
| pt-BR | Português (Brasil) | 葡萄牙語文（巴西） |
| fi | Suomi | 芬蘭文 |
| sv | Svenska | 瑞典文 |


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
