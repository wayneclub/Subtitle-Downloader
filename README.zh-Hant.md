# 字幕下載器

[![en](https://img.shields.io/badge/lang-English-blue)](https://github.com/wayneclub/Subtitle-Downloader/blob/main/README.md) [![python](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/)

**禁止營利使用，只限個人研究和語言學習，字幕版權皆屬原串流平台所有**

字幕下載器支持從各大串流平台下載字幕，例如：Apple TV+、CatchPlay、Crunchyroll、Disney+、friDay影音、HBO GO Asia、愛奇藝、iTunes、KKTV、LINE TV、meWATCH、MyVideo、NowE、NowPlayer、Viki、Viu、WeTV、YouTube 等等。

## 說明

字幕下載器是一個方便您從各大串流平台上下載字幕的程式。需要安裝 **[Python 3.8](https://www.python.org/downloads/)** 以上的版本和 **[NodeJS](https://nodejs.org/en/download)**，可以在 Linux、Windows 或 macOS 上執行。

## 安裝方式

- Linux、macOS:

```bash
pip install -r requriements.txt
```

- Windows：執行`install_requirements.bat`

## 必要驗證資訊

| 名稱 | 驗證方式 | 區域限制 |
| ---- | ------- | ------ |
| Apple TV+ | Cookies | |
| CatchPlay | Cookies | 印尼、新加坡、台灣 |
| Crunchyroll | Cookies | |
| Disney+ | 帳號、密碼 | |
| friDay影音 | Cookies | 台灣 |
| HBO GO Asia | 帳號、密碼 | |
| 愛奇藝 (iq.com) | Cookies | 部分區域 |
| iTunes | | |
| KKTV | | |
| LINE TV | | |
| MeWATCH | Profile Token | Singapore |
| MyVideo | Cookies | 台灣 |
| NowE | Cookies | |
| Now Player | Cookies | |
| Viki | Cookies | 部分區域 |
| Viu | | |
| WeTV | Cookies | 部分區域 |
| YouTube | Cookies（訂閱頻道） | |

### 取得Cookies

1. Chrome安裝[下載cookies](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)的擴充元件
2. 登入串流平台，並利用擴充元件下載 cookies.txt (請勿更改cookies.txt的檔名及其內容)
3. 將 cookie.txt 放入 `Subtitle-Downloader/cookies`

### 帳號、密碼

- 在 `Subtitle-Downloader/user_config.toml` 填入帳號、密碼，方便下次自動下載

## 使用方式

### 線上執行 **_(Colab環境在美國，如果部分串流被限制，請在本機執行)_**

1. 複製一份到自己的雲端
2. 連結 Colab
3. 環境設定，安裝必要程式（執行第ㄧ個按鈕）
4. 依照不同平台填入各項必要資料，填完後按下執行（若需要Cookies，點選左邊側邊欄上傳cookies.txt）
5. 下載的字幕檔案會在左邊側邊欄，可以直接存入Google雲端硬碟或下載到本機

  <a href="https://colab.research.google.com/drive/1ZaGad1httJDw6rut1xmH140UCTlwlBnR?usp=sharing" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" title="Open this file in Google Colab" alt="Colab"/></a>

### 本機執行

1. 可根據要下載的平台修改`user_config.toml`設定檔（設定字幕預設語言、串流平台帳號/密碼等，方便下次直接執行） `Subtitle-Downloader/user_config.toml`

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

2. 根據欲下載不同串流平台的字幕放入對應cookies.txt到`Subtitle-Downloader/cookies`
3. 在終端機執行python指令或是使用`Subtitle-Downloader.bat`下載字幕

    ```bash
    python subtitle_downloader.py 電影、影集的網址 [OPTIONS]
    ```

## 參數

```text
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

HBO GO Asia

| Codec   | Language            | 語言     |
| ------- | ------------------- | -------- |
| en      | English             | 英文     |
| zh-Hant | Traditional Chinese | 繁體中文 |
| zh-Hans | Simplified Chinese  | 簡體中文 |
| ms      | Malay               | 馬來文   |
| th      | Thai                | 泰文     |
| id      | Indonesian          | 印尼文   |

愛奇藝 iq.com

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

## meWATCH

1. 在瀏覽器登錄 [meWATCH](https://www.mewatch.sg/)
2. 選擇要下載的電影或連續劇
3. 在瀏覽器中打開`開發人員工具`（Windows：Ctrl + Shift + I 或 F12；macOS：⌘ + ⌥ + I。）
4. 重新整理網頁，在開發人員工具上選擇`網路`
5. 在篩選器中輸入 `https://www.mewatch.sg/api/account/profile`，找到profile api
6. 複製 profile api 中 Request Headers 的 profile token（X-Authorization）（不要包含 `Bearer`，profile token是"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJ"開頭）貼到 `Subtitle-Downloader/user_config.toml ([credentials.meWATCH] profile_token='')`

## Now E, Now Player

- 從瀏覽器複製 User-Agent [https://www.whatsmyua.info/](https://www.whatsmyua.info/)，並貼在 `Subtitle-Downloader/user_config.toml`(User-Agent). User-Agent必須與登入Now E、Now Player相同。

## 更多範例

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

## 注意

- 部分串流平台有地域限制，可使用代理繞過
- Disney+ 不支援使用 VPN
- Viki 有API限制，別太頻繁呼叫（只下載完成度100%的字幕）

## 常見問題

- 下載字幕過程中若出現任何問題，請上傳截圖和日誌文件（請提供下載的連結、平台和是否使用vpn跨區下載）。
- 回報問題前，請先確保影片有外掛字幕（字幕可關閉）並且可以在您所在的地區正常播放。

## 支持與貢獻

- 如果這個專案對您有幫助，請給我個⭐️！
- 歡迎任何形式的貢獻！

 <a href="https://www.buymeacoffee.com/wayneclub" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/black_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

## 附錄

- Netflix: [Netflix subtitle downloader](https://greasyfork.org/en/scripts/26654-netflix-subtitle-downloader)
- Amazon (Prime Video): [Amazon subtitle downloader](https://greasyfork.org/en/scripts/34885-amazon-video-subtitle-downloader/feedback)
