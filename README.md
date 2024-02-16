# Subtitle Downloader

[![zh](https://img.shields.io/badge/lang-中文-blue)](https://github.com/wayneclub/Subtitle-Downloader/blob/main/README.zh-Hant.md) [![python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)

**NON-COMMERCIAL USE ONLY**

Subtitle-Downloader supports downloading subtitles from multiple streaming services, such as Apple TV+, CatchPlay, Crunchyroll, Disney+, FridayVideo, HBO GO Asia, iQIYI, iTunes, KKTV, LINE TV, meWATCH, MyVideo, NowE, NowPlayer, Viki, Viu, WeTV, YouTube, etc.

## DESCRIPTION

Subtitle-Downloader is a command-line program to download subtitles from the most popular streaming platform. It requires **[Python 3.10+](https://www.python.org/downloads/)**, and **[NodeJS](https://nodejs.org/en/download)**. It should work on Linux, on Windows, or macOS. This project is only for personal research and language learning.

## INSTALLATION

- Linux, macOS:

```bash
pip install -r requirements.txt
```

- Windows: Execute `install_requirements.bat`

## Service Requirements

| Name | Authentication | Geo-blocking |
| ---- | -------------- | ------------ |
| Apple TV+ | Cookies | |
| CatchPlay | Cookies | Indonesia, Singapore, and Taiwan |
| Crunchyroll | Cookies | |
| Disney+ | Email & Password | |
| Friday Video | Cookies | Taiwan |
| HBO GO Asia | Email & Password | |
| iQIYI (iq.com) | Cookies | Partial region |
| iTunes | | |
| KKTV | | |
| LINE TV | | |
| MeWATCH | Profile Token | Singapore |
| MyVideo | Cookies | Taiwan |
| NowE | Cookies | |
| Now Player | Cookies | |
| Viki | Cookies | Partial region |
| Viu | | |
| WeTV | Cookies | Partial region |
| YouTube | Cookies (Subscribe channel) | |

### Get Cookies

1. Install Chrome plugin: [get-cookiestxt-locally](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Login to the streaming service, and use the plugin to download cookies.txt (Don't modify anything even the file name)
3. Put cookie.txt into `Subtitle-Downloader/cookies`

### Email & Password

- Fill your email and password in `Subtitle-Downloader/user_config.toml`

## USAGE

### Online **_(Colab environment is in the US, if you want to use it in another region please execute it locally)_**

1. Save a copy in Drive
2. Connect Colab
3. Install the requirements (Click 1st play button)
4. Depend the download platform and modify the text field  (Click the play button next to it when modified completely)
5. Download the subtitles from the left-side menu

<a href="https://colab.research.google.com/drive/1WdHOKNatft4J7DNOweP4gE2qtg7cvwEf?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a>

### Local

1. Depending on the download platform and modify `Subtitle-Downloader/user_config.toml`

    ```toml
    [subtitles]
    default-language = 'en'  # all/en/zh-Hant/zh-Hans/zh-HK/ja/ko
    default-format = '.srt'  # .srt/.ass
    archive = true           # true/false

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

2. Follow each platform's requirements and put cookies.txt into `Subtitle-Downloader/cookies`
3. Execute the program with the command line or `Subtitle-Downloader.bat` (Paste the title's URL)

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

  -locale, --locale             interface language

  -p, --proxy                   proxy

  -d, --debug                   enable debug logging

  -v, --version                 app's version
```

## Subtitle Languages

Disney+

| Codec         | Language                           |
| ------------- | ---------------------------------- |
| en            | English [CC]                       |
| zh-Hant       | Chinese (Traditional)              |
| zh-Hans       | Chinese (Simplified)               |
| zh-HK         | Cantonese                          |
| da            | Dansk                              |
| de            | Deutsch                            |
| de-forced     | Deutsch [forced]                   |
| es-ES         | Español                            |
| es-ES-forced  | Español [forced]                   |
| es-419        | Español (Latinoamericano)          |
| es-419-forced | Español (Latinoamericano) [forced] |
| fr-FR         | Français                           |
| fr-FR-forced  | Français [forced]                  |
| fr-CA         | Français (Canadien)                |
| fr-CA-forced  | Français (Canadien) [forced]       |
| it            | Italiano                           |
| it-forced     | Italiano [forced]                  |
| ja            | Japanese                           |
| ja-forced     | Japanese [forced]                  |
| ko            | Korean                             |
| ko-forced     | Korean [forced]                    |
| nl            | Nederlands                         |
| no            | Norsk                              |
| pl            | Polski                             |
| pl-forced     | Polski [forced]                    |
| pt-PT         | Português                          |
| pt-BR         | Português (Brasil)                 |
| pt-BR-forced  | Português (Brasil) [forced]        |
| fi            | Suomi                              |
| sv            | Svenska                            |

HBO GO Asia

| Codec   | Language            |
| ------- | ------------------- |
| en      | English             |
| zh-Hant | Traditional Chinese |
| zh-Hans | Simplified Chinese  |
| ms      | Malay               |
| th      | Thai                |
| id      | Indonesian          |

iQIYI iq.com

| Codec   | Language            |
| ------- | ------------------- |
| en      | English             |
| zh-Hant | Traditional Chinese |
| zh-Hans | Simplified Chinese  |
| ms      | Malay               |
| vi      | Vietnamese          |
| th      | Thai                |
| id      | Indonesian          |
| es      | Spanish             |
| ko      | Korean              |
| ar      | Arabic              |

Viu
| Codec | Language |
| --- | --- |
| en | English |
| zh-Hant | Traditional Chinese |
| zh-Hans | Simplified Chinese |
| ms | Malay |
| th | Thai |
| id | Indonesian |
| my | Burmese |

WeTV
| Codec | Language |
| --- | --- |
| en | English |
| zh-Hant | Traditional Chinese |
| zh-Hans | Simplified Chinese |
| ms |
| th | Thai |
| id | Indonesian |
| pt | Português |
| es | Spanish |
| ko | Korean |

## meWATCH

1. Login to [meWATCH](https://www.mewatch.sg/) on the browser.
2. Select a movie or series you want to download
3. Open the `devtools` in the browser (Windows: Ctrl + Shift + I or F12; macOS: ⌘ + ⌥ + I.)
4. Refresh the page and select `Network` on `devtools`
5. Type `https://www.mewatch.sg/api/account/profile` in the filter to find the profile api
6. Copy profile token (X-Authorization) from profile API Request Headers (Do not include `Bearer`, the profile token starts with `eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJ`) and paste in `Subtitle-Downloader/user_config.toml ([credentials.meWATCH] profile_token='')`.

## Now E, Now Player

- Copy the user-agent from login browser [https://www.whatsmyua.info/](https://www.whatsmyua.info/) and paste it in `Subtitle-Downloader/user_config.toml (User-Agent)`. The user-agent must be the same as login browser user-agent.

## More Examples

- Download all seasons and all episodes

```bash
python subtitle_downloader.py URL
```

- Download season 1 episode 1

```bash
python subtitle_downloader.py URL -s 1 -e 1
```

- Download season 1 episode 1's subtitle with all languages

```bash
python subtitle_downloader.py URL -s 1 -e 1 -slang all
```

- Download all episode subtitles in all languages: en, zh-Hant

```bash
python subtitle_downloader.py https://www.disneyplus.com/series/loki/6pARMvILBGzF -slang en,zh-Hant
```

- Download the latest episode

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

- Any issue during downloading subtitles, upload the screenshot and log file (Please provide title, platform, and region).
- Make sure the video contains embedded subtitles (subtitles able to turn on and off) and it is playable in your region.

## Support & Contributions

- Please ⭐️ this repository if this project helped you!
- Contributions of any kind are welcome!

 <a href="https://www.buymeacoffee.com/wayneclub" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/black_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

## Appendix

- Netflix: [Netflix subtitle downloader](https://greasyfork.org/en/scripts/26654-netflix-subtitle-downloader)
- Amazon (Prime Video): [Amazon subtitle downloader](https://greasyfork.org/en/scripts/34885-amazon-video-subtitle-downloader/feedback)
