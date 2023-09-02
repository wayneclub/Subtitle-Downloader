# Subtitle Downloader

[![en](https://img.shields.io/badge/lang-English-blue)](https://github.com/wayneclub/Subtitle-Downloader/blob/main/README.md) [![python](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/)

**禁止營利使用，只限個人研究和語言學習，字幕版權皆屬原串流平台所有**

Subtitle-Downloader 支持從各大串流平台下載字幕，例如：Disney Plus、HBOGO Asia、KKTV、LineTV、friDay影音、MyVideo、CatchPlay、iq.com（愛奇藝）、Viu（不需要VPN即可下載香港、新加坡地區的字幕）、WeTV、NowE、Now Player、AppleTV Plus、iTunes等等。

## 說明

Subtitle-Downloader 是一個方便您從各大串流平台上下載字幕的程式。需要安裝 [Python](https://www.python.org/downloads/)3.8以上的版本和 [NodeJS](https://nodejs.org/en/download)，可以在 Linux、Windows 或 macOS 上執行。

## 安裝方式

- Linux、macOS:
```
pip install -r requriements
```

- Windows：執行install_requirements.bat

## 必要驗證資訊

| Name | 驗證方式 |
| ---- | ------- |
| Apple TV+ | Cookies |
| CatchPlay | Cookies |
| Disney+ | 帳號、密碼 |
| Friday影音 | Cookies |
| HBOGO Asia | 帳號、密碼 |
| 愛奇藝 (iq.com) | Cookies |
| iTunes |  |
| KKTV |  |
| LineTV |  |
| MyVideo | Cookies |
| NowE | Cookies |
| Now Player | Cookies |
| Viu |  |
| WeTV | Cookies |

### 取得Cookies

1. Chrome安裝擴充元件 https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. 登入串流平台，並利用擴充元件下載 cookies.txt (請勿更改cookies.txt的檔名及其內容)
3. 將 cookie.txt 放入 Subtitle-Downloader/cookies

### 帳號、密碼

- 在 Subtitle-Downloader/user_config.toml 填入帳號、密碼，方便下次自動下載

## 使用方式

- 線上執行 **_(Colab環境在美國，如果部分串流被限制，請在本機執行)_**
  1. 連結 Colab
  2. 環境設定，安裝必要程式 (執行第ㄧ個按鈕)
  3. 依照不同平台填入各項必要資料 (執行其他按鈕)
  4. 下載的字幕檔案會在左邊側邊欄，可以直接存入Google雲端硬碟或下載到本機

    <a href="https://colab.research.google.com/drive/1ZaGad1httJDw6rut1xmH140UCTlwlBnR?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a>


- 本機執行

  1. 可根據要下載的平台修改user_config.toml設定檔（設定字幕預設語言、串流平台帳號/密碼等，方便下次直接執行） Subtitle-Downloader/user_config.toml
  2. 根據欲下載不同串流平台的字幕放入對應cookies.txt到Subtitle-Downloader/cookies
  3. 在終端機執行python指令或是使用Subtitle-Downloader.bat下載字幕

  ```
  python subtitle_downloader.py 電影、影集的網址 [OPTIONS]
  ```

## 參數

```
  -h, --help                    參數說明

  -s --season                   下載 第[0-9]季

  -e --episode                  下載 第[0-9]集

  -l, --last-episode            下載 最新一集

  -o, --output                  下載路徑

  -slang, --subtitle-language   字幕語言，用','分隔
                                預設: 繁體中文
                                all: 下載所有語言

  -alang, --audio-language      音軌語言，用','分隔

  -sf, --subtitle-format        字幕格式：.srt 或 .ass

  -region, --region             串流平台地區

  -locale, --locale             界面語言

  -p, --proxy                   代理

  -d, --debug                   除錯日誌

  -v, --version                 程式版本
```

## 字幕語言

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

HBOGO Asia

| Codec   | Language            | 語言     |
| ------- | ------------------- | -------- |
| en      | English             | 英文     |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese  | 簡體中文 |
| ms      | Malay               | 馬來文   |
| th      | Thai                | 泰文     |
| id      | Indonesian          | 印尼文   |

iq.com

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

- 從瀏覽器複製 User-Agent (https://www.whatsmyua.info/)，並貼在 Subtitle-Downloader/user_config.toml (User-Agent). User-Agent必須與登入Now E、Now Player相同。


## 更多範例
- Download all seasons and all episodes
```
python subtitle_downloader.py URL
```

- Download season 1 episode 1
```
python subtitle_downloader.py URL -s 1 -e 1
```

- Download season 1 episode 1's subtitle with all langugages
```
python subtitle_downloader.py URL -s 1 -e 1 -slang all
```

- Download all episodes subtitles with all langugages: en, zh-Hant
```
python subtitle_downloader.py https://www.disneyplus.com/series/loki/6pARMvILBGzF -slang en,zh-Hant
```

- Download latest episode
```
python subtitle_downloader.py URL -l
```

- Download season 1 episode 1-10
```
python subtitle_downloader.py URL -s 1 -e 1-10
```

- Download season 1 episode 1,3,5
```
python subtitle_downloader.py URL -s 1 -e 1,3,5
```

- Download season 1 with proxy (clash)
```
python subtitle_downloader.py URL -p http://127.0.0.1:7890
```

## 注意

- 部分串流平台有地域限制，可使用代理繞過
- Disney+ 不支援使用 VPN

## 常見問題

- 下載字幕過程中若出現任何問題，請上傳截圖和日誌文件（請提供下載的連結、平台和是否使用vpn跨區下載）。
- 回報問題前，請先確保影片有外掛字幕（字幕可關閉）並且可以在您所在的地區正常播放。