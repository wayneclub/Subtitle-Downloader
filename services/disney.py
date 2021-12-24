"""
This module is to download subtitle from Disney+
"""

import re
import os
import math
import shutil
import time
import m3u8
from selenium.webdriver.common.by import By
from common.utils import get_dynamic_html, get_network_url, get_static_html, download_audio, find_visible_element_by_id,  find_visible_element_clickable_by_xpath, download_file, convert_subtitle, merge_subtitle

BASE_URL = "https://www.disneyplus.com"
LOGIN_URL = f"{BASE_URL}/login"
SELECT_PROFILE_URL = f"{BASE_URL}/select-profile"


def login(email="", password=""):
    driver = get_dynamic_html(LOGIN_URL)
    print("登入Disney+...")

    email_input = find_visible_element_by_id(driver, 'email')
    email_input.send_keys(email)
    find_visible_element_clickable_by_xpath(
        driver, "//button[@data-testid='login-continue-button']").click()
    email = ''

    time.sleep(1)

    password_input = find_visible_element_by_id(driver, 'password')
    cookie_button = driver.find_elements(
        By.XPATH, "//button[@id='onetrust-accept-btn-handler']")
    if cookie_button:
        cookie_button[0].click()
    password_input.send_keys(password)
    find_visible_element_clickable_by_xpath(
        driver, "//button[@data-testid='password-continue-login']").click()
    password = ''

    time.sleep(3)

    driver.refresh()

    time.sleep(1)

    username = ''
    if '/select-profile' in driver.current_url:
        user = find_visible_element_clickable_by_xpath(
            driver, "//div[@data-testid='profile-avatar-0']")
        username = user.text
        user.click()
    else:
        driver.get(SELECT_PROFILE_URL)
        user = find_visible_element_clickable_by_xpath(
            driver, "//div[@data-testid='profile-avatar-0']")
        username = user.text
        user.click()

    time.sleep(3)

    if '/home' in driver.current_url:
        print(
            f"登入成功...\n歡迎 {username} 使用Disney+\n---------------------------------------------------------------")
    else:
        print(driver.current_url)

    return driver


def download_subtitle(driver, url, genre, output="", download_season="", language="", audio=""):

    if not language:
        language = 'zh-Hant'
    elif language == 'all':
        language = 'en,zh-Hant,zh-HK'
    if ',' not in language:
        lang_list = list(language)
    lang_list = language.split(',')

    series_url = f'https://disney.content.edge.bamgrid.com/svc/content/DmcSeriesBundle/version/5.1/region/TW/audience/false/maturity/1850/language/zh-Hant/encodedSeriesId/{os.path.basename(url)}'

    data = get_static_html(series_url, True)['data']['DmcSeriesBundle']
    drama_name = data['series']['text']['title']['full']['series']['default']['content']

    if genre == 'series':
        seasons = data['seasons']['seasons']

        season_start = 0
        season_end = len(seasons)

        if download_season:
            if int(download_season) > 0 and int(download_season) <= len(seasons):
                season_start = int(download_season)-1
            else:
                print(
                    f"\n{drama_name} 只有{len(seasons)}季，沒有第 {int(download_season)} 季")
                exit(1)

        print(f"\n{drama_name} 共有：{len(seasons)} 季")

        travel_button = driver.find_elements(
            By.XPATH, "//button[@data-testid='modal-primary-button']")
        if travel_button:
            travel_button[0].click()

        for season in seasons[season_start:season_end]:
            season_index = season['seasonSequenceNumber']
            season_name = str(season_index).zfill(2)
            episode_num = season['episodes_meta']['hits']
            episode_list = check_episodes(season, series_url)

            folder_path = os.path.join(
                output, f'{drama_name}.S{season_name}')

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            print(
                f"\n第 {season_index} 季 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")

            for episode_index, episode_id in enumerate(episode_list, start=1):
                time.sleep(1)
                episode_name = str(episode_index).zfill(2)

                episode_url = f'https://www.disneyplus.com/zh-hant/video/{episode_id}'
                driver.get(episode_url)

                print(
                    f"尋找第 {season_index} 季 第 {episode_index} 集字幕中...")

                m3u_url = get_network_url(driver, r'ctr-all.+\.m3u')
                file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.Disney+'
                subtitle_list, audio_list = parse_m3u(m3u_url)
                get_subtitle(subtitle_list, genre,
                             folder_path, file_name, lang_list)
                if audio:
                    get_audio(audio_list, folder_path, file_name)
            print(folder_path)
            convert_subtitle(folder_path, 'disney')
    elif genre == 'movies':
        print(drama_name)
        folder_path = os.path.join(output, drama_name)
        file_name = f'{drama_name}.WEB-DL.Disney+'
        find_visible_element_clickable_by_xpath(
            driver, "//button[@data-testid='play-button']").click()

        print(
            f"尋找{drama_name}字幕中...")
        m3u_url = get_network_url(driver, r'ctr-all.+\.m3u')
        subtitle_list, audio_list = parse_m3u(m3u_url)
        get_subtitle(subtitle_list, genre,
                     folder_path, file_name, lang_list)
        if audio:
            get_audio(audio_list, folder_path, file_name)
    driver.quit()


def check_episodes(season, series_url):
    episode_num = season['episodes_meta']['hits']
    episodes = season['downloadableEpisodes']
    if len(episodes) != episode_num:
        season_id = season['seasonId']
        page_size = math.ceil(len(episodes) / 15)
        episodes = []
        for page in range(1, page_size+1):
            episode_page_url = re.sub(r'(.+)DmcSeriesBundle(.+)encodedSeriesId.+',
                                      '\\1DmcEpisodes\\2seasonId/', series_url) + f'{season_id}/pageSize/15/page/{page}'
            for episode in get_static_html(episode_page_url, True)['data']['DmcEpisodes']['videos']:
                episodes.append(episode['contentId'])
    return episodes


def parse_m3u(m3u_link):
    base_url = os.path.dirname(m3u_link)
    sub_url_list = []
    audio_url_list = []

    playlists = m3u8.load(m3u_link).playlists
    quality_list = [
        playlist.stream_info.bandwidth for playlist in playlists]
    best_quality = quality_list.index(max(quality_list))

    # print(playlists[best_quality].stream_info)

    for media in playlists[best_quality].media:
        if media.type == 'SUBTITLES' and media.group_id == 'sub-main' and not 'forced' in media.name:
            sub = {}
            sub['lang'] = media.language
            m3u_sub = m3u8.load(os.path.join(base_url, media.uri))
            sub['urls'] = []
            for segement in re.findall(r'.+\-MAIN\/.+\.vtt', m3u_sub.dumps()):
                sub['urls'].append(os.path.join(
                    f'{base_url}/r/', segement))
            sub_url_list.append(sub)
        if media.type == 'AUDIO' and not 'Audio Description' in media.name:
            audio = {}
            if media.group_id == 'eac-3':
                audio['url'] = os.path.join(base_url, media.uri)
                audio['extension'] = '.eac3'
            elif media.group_id == 'aac-128k':
                audio['url'] = os.path.join(base_url, media.uri)
                audio['extension'] = '.aac'
            audio['lang'] = media.language
            audio_url_list.append(audio)
    return sub_url_list, audio_url_list


def get_subtitle(subtitle_list, genre, folder_path, sub_name, lang_list):
    for sub in subtitle_list:
        if sub['lang'] in lang_list:
            file_name = f"{sub_name}.{sub['lang']}.srt"
            tmp_folder_path = os.path.join(
                os.path.join(folder_path, sub['lang']), 'tmp')
            print(f"下載：{file_name}")

            if genre == 'movies' or len(lang_list) == 1:
                tmp_folder_path = os.path.join(folder_path, 'tmp')

            if os.path.exists(tmp_folder_path):
                shutil.rmtree(tmp_folder_path)
            os.makedirs(tmp_folder_path, exist_ok=True)
            for segement_url in sub['urls']:
                download_file(segement_url, os.path.join(
                    tmp_folder_path, os.path.basename(segement_url)))
            print()
            convert_subtitle(tmp_folder_path)
            merge_subtitle(tmp_folder_path, file_name)


def get_audio(audio_list, folder_path, audio_name):
    for audio in audio_list:
        if audio['lang'] in ['cmn-TW', 'yue']:
            file_name = f"{audio_name}.{audio['lang']}{audio['extension']}"
            print(f"下載：{file_name}")
            download_audio(audio['url'], os.path.join(
                folder_path, file_name))
