# Subtitle Downloader

[![zh](https://img.shields.io/badge/lang-中文-blue)](https://github.com/wayneclub/Subtitle-Downloader/blob/main/README.zh-Hant.md) [![python](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/)

**NON-COMMERCIAL USE ONLY**

Subtitle-Downloader supports downloading subtitles from multiple streaming services, such as Apple TV+, CatchPlay, Disney+, FridayVideo, HBO GO Asia, iQIYI, iTunes, KKTV, LINE TV,
meWATCH, MyVideo, NowE, NowPlayer, Viki, Viu, WeTV, YouTube, and etc.

## DESCRIPTION

Subtitle-Downloader is a command-line program to download subtitles from the most popular streaming platform. It requires [Python 3.8+](https://www.python.org/downloads/), and [NodeJS](https://nodejs.org/en/download). It should work on Linux, on Windows or on macOS. This project is only for personal research and language learning.

## INSTALLATION

- Linux, macOS:

```bash
pip install -r requriements
```

- Windows: Execute `install_requirements.bat`

## Service Requirements

| Name | Authentication | Geo-blocking |
| ---- | -------------- | ------------ |
| Apple TV+ | Cookies |  |
| CatchPlay | Cookies | Indonesia, Singapore, and Taiwan |
| Disney+ | Email & Password |  |
| Friday Video | Cookies | Taiwan |
| HBO GO Asia | Email & Password |  |
| iQIYI (iq.com) | Cookies | Partial region |
| iTunes |  |  |
| KKTV |  |  |
| LINE TV |  |  |
| MeWATCH | Email & Password | Singapore |
| MyVideo | Cookies | Taiwan |
| NowE | Cookies |  |
| Now Player | Cookies |  |
| Viki | Cookies | Partial region |
| Viu |  |  |
| WeTV | Cookies | Partial region |
| YouTube | Cookies (Subscribe channel) |  |

### Get Cookies

1. Install Chrome plugin: [get-cookiestxt-locally](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Login to the streaming service, and use the plugin to download cookies.txt (Don't modify anything even the file name)
3. Put cookie.txt into `Subtitle-Downloader/cookies`

### Email & Password

- Fill your email and password in `Subtitle-Downloader/user_config.toml`

## USAGE

### Online **_(Colab environment is in the US, if you want to use in other region please execute on local)_**

1. Save a copy in Drive
2. Connect Colab
3. Install the requirements (Click 1st play button)
4. Depend the download platform and modify the text field  (Cick the play button next to it when modified complete)
5. Download the subtitles from the left side menu

<a href="https://colab.research.google.com/drive/1Qu7MHUt4QXym9cNOORCKTezIBYBNNg3V?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a>

### Local

1. Depend on download platform and modify `Subtitle-Downloader/user_config.toml`

    ```toml
    [subtitles]
    default-language = 'en'
    default-format = '.srt'

    [headers]
    User-Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'

    [credentials.DisneyPlus]
    email = ''
    password = ''

    [proxies]
    us = 'http:127.0.0.1:7890' # Clash

    [nordvpn]
    username = ''
    password = ''
    ```

2. Follow each platform requirements and put cookies.txt into `Subtitle-Downloader/cookies`
3. Execute the program with command line or `Subtitle-Downloader.bat` (Paste title url)

    ```bash
    python subtitle_downloader.py URL [OPTIONS]
    ```

## OPTIONS

```text
  -h, --help                    show this help message and exit

  -s --season                   download season [0-9]

  -e --episode                  download episode [0-9]

  -l, --last-episode            download last episode

  -o, --output                  output directory

  -slang, --subtitle-language   languages of subtitles; use commas to separate multiple languages
                                default: Traditional Chinese
                                all: download all available languages

  -alang, --audio-language      languages of audio-tracks; use commas to separate multiple languages

  -sf, --subtitle-format        subtitles format: .srt or .ass

  -region, --region             streaming service's region

  -locale, --locale             interface language

  -p, --proxy                   proxy

  -d, --debug                   enable debug logging

  -v, --version                 app's version
```

## Subtitle Languages

Disney+

| Codec         | Language                           | 語言                         |
| ------------- | ---------------------------------- | ---------------------------- |
| en            | English [CC]                       | 英文                         |
| zh-Hant       | Chinese (Traditional)              | 台繁                         |
| zh-Hans       | Chinese (Simplified)               | 簡中                         |
| zh-HK         | Cantonese                          | 港繁                         |
| da            | Dansk                              | 丹麥文                       |
| de            | Deutsch                            | 德文                         |
| de-forced     | Deutsch [forced]                   | 德文 [強制軌]                |
| es-ES         | Español                            | 西班牙文                     |
| es-ES-forced  | Español [forced]                   | 西班牙文 [強制軌]            |
| es-419        | Español (Latinoamericano)          | 西班牙文（拉丁美洲）         |
| es-419-forced | Español (Latinoamericano) [forced] | 西班牙文（拉丁美洲）[強制軌] |
| fr-FR         | Français                           | 法文                         |
| fr-FR-forced  | Français [forced]                  | 法文 [強制軌]                |
| fr-CA         | Français (Canadien)                | 法文（加拿大）               |
| fr-CA-forced  | Français (Canadien) [forced]       | 法文（加拿大）[強制軌]       |
| it            | Italiano                           | 義大利文                     |
| it-forced     | Italiano [forced]                  | 義大利文 [強制軌]            |
| ja            | Japanese                           | 日文                         |
| ja-forced     | Japanese [forced]                  | 日文 [強制軌]                |
| ko            | Korean                             | 韓文                         |
| ko-forced     | Korean [forced]                    | 韓文 [強制軌]                |
| nl            | Nederlands                         | 荷蘭文                       |
| no            | Norsk                              | 挪威文                       |
| pl            | Polski                             | 波蘭文                       |
| pl-forced     | Polski [forced]                    | 波蘭文 [強制軌]              |
| pt-PT         | Português                          | 葡萄牙文                     |
| pt-BR         | Português (Brasil)                 | 葡萄牙文（巴西）             |
| pt-BR-forced  | Português (Brasil) [forced]        | 葡萄牙文（巴西）[強制軌]     |
| fi            | Suomi                              | 芬蘭文                       |
| sv            | Svenska                            | 瑞典文                       |

HBO GO Asia

| Codec   | Language            | 語言     |
| ------- | ------------------- | -------- |
| en      | English             | 英文     |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese  | 簡體中文 |
| ms      | Malay               | 馬來文   |
| th      | Thai                | 泰文     |
| id      | Indonesian          | 印尼文   |

iQIYI iq.com

| Codec   | Language            | 語言     |
| ------- | ------------------- | -------- |
| en      | English             | 英文     |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese  | 簡體中文 |
| ms      | Malay               | 馬來文   |
| vi      | Vietnamese          | 越南文   |
| th      | Thai                | 泰文     |
| id      | Indonesian          | 印尼文   |
| es      | Spanish             | 西班牙文 |
| ko      | Korean              | 韓文     |
| ar      | Arabic              | 阿拉伯文 |

Viu
| Codec | Language | 語言 |
| --- | --- | --- |
| en | English | 英文 |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese | 簡體中文 |
| ms | Malay | 馬來文 |
| th | Thai | 泰文 |
| id | Indonesian | 印尼文 |
| my | Burmese | 緬甸文 |

WeTV
| Codec | Language | 語言 |
| --- | --- | --- |
| en | English | 英文 |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese | 簡體中文 |
| ms | Malay | 馬來文 |
| th | Thai | 泰文 |
| id | Indonesian | 印尼文 |
| pt | Português | 葡萄牙文 |
| es | Spanish | 西班牙文 |
| ko | Korean | 韓文 |

## Now E, Now Player

- Copy user-agent from login browser [https://www.whatsmyua.info/](https://www.whatsmyua.info/) and paste it in `Subtitle-Downloader/user_config.toml (User-Agent)`. The user-agent must be same as login browser user-agent.

## More Examples

- Download all seasons and all episodes

```bash
python subtitle_downloader.py URL
```

- Download season 1 episode 1

```bash
python subtitle_downloader.py URL -s 1 -e 1
```

- Download season 1 episode 1's subtitle with all langugages

```bash
python subtitle_downloader.py URL -s 1 -e 1 -slang all
```

- Download all episodes subtitles with all langugages: en, zh-Hant

```bash
python subtitle_downloader.py https://www.disneyplus.com/series/loki/6pARMvILBGzF -slang en,zh-Hant
```

- Download latest episode

```bash
python subtitle_downloader.py URL -l
```

- Download season 1 episode 1-10

```bash
python subtitle_downloader.py URL -s 1 -e 1-10
```

- Download season 1 episode 1,3,5

```bash
python subtitle_downloader.py URL -s 1 -e 1,3,5
```

- Download season 1 episodes with NordVPN (region=tw)

```bash
python subtitle_downloader.py URL -s 1 -p tw
```

- Download season 1 episodes with proxy (Clash)

```bash
python subtitle_downloader.py URL -s 1 -p http:127.0.0.1:7890
```

- Download season 1 episodes with .ass format subtitle

```bash
python subtitle_downloader.py URL -s 1 -sf .ass
```

## NOTICE

- Few streaming services have Geo-blocking, make sure you are in the same region or use a proxy to bypass restrictions.
- Disney+ doesn't support VPN.
- Viki has API protection, don't call API too often. (Only catch 100% completed subtitles)

## FAQ

- Any issue during downloading subtitles, upload the screenshot and log file (Please provide title, platform and region).
- Make sure the video contains embedded subtitles (subtitles able to turn on-off) and it is playable in your region.


## Appendix

- Netflix: [Netflix subtitle downloader](https://greasyfork.org/en/scripts/26654-netflix-subtitle-downloader)
- Amazon (Prime Video): [Amazon subtitle downloader](https://greasyfork.org/en/scripts/34885-amazon-video-subtitle-downloader/feedback)
