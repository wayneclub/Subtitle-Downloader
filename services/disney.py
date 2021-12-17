"""
This module is to download subtitle from Disney+
"""

import re
import os
import shutil
import time
import m3u8
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from common.utils import get_dynamic_html, download_audio, find_visible_element_by_id, find_visible_element_by_xpath, find_visible_element_clickable_by_xpath, find_present_element_by_xpath, download_file, convert_subtitle, merge_subtitle, save_html

BASE_URL = "https://www.disneyplus.com"
LOGIN_URL = f"{BASE_URL}/zh-hant/login"
SELECT_PROFILE_URL = f"{BASE_URL}/zh-hant/select-profile"


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
    password_input.send_keys(password)
    find_visible_element_clickable_by_xpath(
        driver, "//button[@data-testid='password-continue-login']").click()
    password = ''

    time.sleep(3)

    username = ''
    if '/select-profile' in driver.current_url:
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
    driver.get(url)

    if WebDriverWait(driver, 10).until(EC.url_to_be(url)):

        if WebDriverWait(driver, 10, 0.5).until(EC.title_contains('觀看')):
            # drama_name = re.sub(r'(觀看|Watch )(.+) \|.+',
            #                     '\\2', driver.title).strip()
            drama_name = find_present_element_by_xpath(
                driver, '//h1').text.strip()
        # drama_name = re.sub(r'Watch (.+) \| Disney\+', '\\1', driver.title)
        if not language:
            language = 'zh-Hant'
        elif language == 'all':
            language = 'en,zh-Hant,zh-HK'
        if ',' not in language:
            lang_list = list(language)
        lang_list = language.split(',')

        time.sleep(1)

        if genre == 'series':
            if find_visible_element_by_xpath(driver, "//button[contains(@data-testid, 'season')]"):
                season_buttons = driver.find_elements_by_xpath(
                    "//button[contains(@data-testid, 'season')]")

                season_start = 0
                season_end = len(season_buttons)

            if download_season:
                if int(download_season) > 0 and int(download_season) <= len(season_buttons):
                    season_start = int(download_season)-1
                else:
                    print(
                        f"\n{drama_name} 只有{len(season_buttons)}季，沒有第 {int(download_season)} 季")
                    exit(1)

            print(f"\n{drama_name} 共有：{len(season_buttons)} 季")
            print(season_buttons)

            season_list = []
            for season_button in season_buttons[season_start:season_end]:
                total_episode = season_button.get_attribute(
                    'aria-label').replace('。', '').replace('，', '：')
                time.sleep(1)
                if season_button.is_enabled():
                    season_button.click()
                    time.sleep(1)

                save_html(driver.page_source)

                if len(driver.find_elements(By.XPATH, "//div[@data-program-type='episode']")) != int(re.sub(r'第\d+季：(\d+)集', '\\1', total_episode)):
                    click = True
                    while click and len(driver.find_elements(By.XPATH, "//div[@data-program-type='episode']")) > 4:
                        time.sleep(1)
                        print('enter')
                        next_button = find_present_element_by_xpath(
                            driver, "//button[@data-testid='arrow-right']")

                        if int(next_button.get_attribute('tabindex')) == 0:
                            print('moving')
                            ActionChains(driver).move_to_element(
                                next_button).click(next_button).perform()
                            print(next_button.get_attribute('class'))
                        else:
                            click = False

                web_content = BeautifulSoup(driver.page_source, 'lxml')
                episode_list = web_content.find_all(
                    'div', {'data-program-type': 'episode'})
                print(episode_list)
                season_list.append(episode_list)

            for season_num, season in enumerate(season_list, start=1):
                if download_season:
                    season_num = download_season
                season_name = str(season_num).zfill(2)
                folder_path = f'{output}{drama_name}.S{season_name}'

                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                print(
                    f"\n第 {int(season_num)} 季 共有：{len(season)} 集\t下載全集\n---------------------------------------------------------------")

                for index, episode in enumerate(season, start=1):
                    time.sleep(1)
                    episode_name = str(index).zfill(2)

                    episode_id = episode.find('a')['data-gv2elementvalue']
                    episode_url = f'https://www.disneyplus.com/zh-hant/video/{episode_id}'
                    driver.get(episode_url)

                    print(
                        f"尋找第 {int(season_name)} 季 第 {int(episode_name)} 集字幕中...")

                    m3u_url = get_m3u8(driver)
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
            folder_path = f'{output}{drama_name}'
            file_name = f'{drama_name}.WEB-DL.Disney+'
            find_visible_element_clickable_by_xpath(
                driver, "//button[@data-testid='play-button']").click()

            print(
                f"尋找{drama_name}字幕中...")
            m3u_url = get_m3u8(driver)
            subtitle_list, audio_list = parse_m3u(m3u_url)
            get_subtitle(subtitle_list, genre,
                         folder_path, file_name, lang_list)
            if audio:
                get_audio(audio_list, folder_path, file_name)
        driver.quit()


def get_m3u8(driver):
    m3u_file = ''
    delay = 0
    logs = []
    while not m3u_file:
        time.sleep(2)
        logs += driver.execute_script(
            "return window.performance.getEntries();")

        m3u_file = next((log for log in logs
                         if re.search(r'ctr-all.+\.m3u', log['name'])), None)
        # print(m3u_file)
        delay += 1

        if delay > 60:
            print("找不到m3u8，請重新執行")
            exit(1)

    return m3u_file


def parse_m3u(m3u_file):
    if m3u_file:
        m3u_link = m3u_file['name']
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
            tmp_folder_path = os.path.join(folder_path, f"{sub['lang']}/tmp")
            print(f"下載：{file_name}")

            if genre == 'movies' or len(lang_list) == 1:
                tmp_folder_path = os.path.join(folder_path, 'tmp')

            if os.path.exists(tmp_folder_path):
                shutil.rmtree(tmp_folder_path)
            os.makedirs(os.path.dirname(
                tmp_folder_path + '/'), exist_ok=True)
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
