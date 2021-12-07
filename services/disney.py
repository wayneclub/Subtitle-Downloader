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
from common.utils import find_visible_element_by_id, find_visible_element_by_xpath, find_visible_element_clickable_by_xpath, find_present_element_by_xpath, download_file, convert_subtitle, merge_subtitle


def download_subtitle(driver, url, email="", password="", output="", download_season="", language=""):

    print("登入Disney+...")

    email_input = find_visible_element_by_id(driver, 'email')
    email_input.send_keys(email)
    find_visible_element_clickable_by_xpath(
        driver, "//button[@data-testid='login-continue-button']").click()
    email = ''

    password_input = find_visible_element_by_id(driver, 'password')
    password_input.send_keys(password)
    find_visible_element_clickable_by_xpath(
        driver, "//button[@data-testid='password-continue-login']").click()
    password = ''
    time.sleep(5)

    if driver.current_url == 'https://www.disneyplus.com/zh-hant/select-profile':
        find_visible_element_clickable_by_xpath(
            driver, "//div[@data-testid='profile-avatar-0']").click()
        time.sleep(2)

    if WebDriverWait(driver, 10).until(EC.url_matches('https://www.disneyplus.com/zh-hant/home')):
        print("登入成功...")

    driver.get(url)

    if WebDriverWait(driver, 10).until(EC.url_to_be(url)):

        if WebDriverWait(driver, 10, 0.5).until(EC.title_contains('觀看')):
            drama_name = re.sub(r'觀看(.+) \| Disney\+', '\\1', driver.title)
        # drama_name = re.sub(r'Watch (.+) \| Disney\+', '\\1', driver.title)

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
                    f"\n該劇只有{len(season_buttons)}季，沒有第 {int(download_season)} 季")
                exit(1)

        print(f"\n{drama_name} 共有：{len(season_buttons)} 季")

        if not language:
            language = 'zh-Hant'
        elif language == 'all':
            language = 'en,zh-Hant,zh-HK'
        if ',' not in language:
            lang_list = list(language)
        lang_list = language.split(',')

        season_list = []
        for season_button in season_buttons[season_start:season_end]:
            time.sleep(1)
            if len(season_buttons) > 1:
                season_button.click()
                time.sleep(1)

            click = True
            while click and len(driver.find_elements(By.XPATH, "//div[@data-program-type='episode']")) > 4:
                next_button = find_present_element_by_xpath(
                    driver, "//button[@data-testid='arrow-right']")
                if int(next_button.get_attribute('tabindex')) == 0:
                    next_button.click()
                else:
                    click = False

            web_content = BeautifulSoup(driver.page_source, 'lxml')
            episode_list = web_content.find_all(
                'div', {'data-program-type': 'episode'})
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

                m3u_file = ''
                delay = 0

                print(f"尋找第 {int(season_name)} 季 第 {int(episode_name)} 集字幕中...")
                logs = []
                while not m3u_file:
                    time.sleep(2)
                    logs += driver.execute_script(
                        "return window.performance.getEntries();")

                    m3u_file = next((log for log in logs
                                     if re.search(r'ctr-all.+\.m3u', log['name'])), None)
                    # print(m3u_file)
                    delay += 1

                    if delay % 10 == 0:
                        driver.refresh()
                    elif delay > 60:
                        print("找不到字幕，請重新執行")
                        exit(1)

                if m3u_file:
                    m3u_link = m3u_file['name']
                    base_url = os.path.dirname(m3u_link)

                    tmp_folder_path = os.path.join(folder_path, 'tmp')
                    en_tmp_folder_path = os.path.join(folder_path, '英語/tmp')
                    hk_tmp_folder_path = os.path.join(folder_path, '港繁/tmp')

                    for media in m3u8.load(m3u_link).playlists[0].media:
                        if media.type == 'SUBTITLES' and media.group_id == 'sub-main' and (media.name == 'English [CC]' or media.name == 'Chinese (Traditional)' or media.name == 'Chinese (Hong Kong)'):

                            if media.language in lang_list:
                                m3u_sub = m3u8.load(
                                    os.path.join(base_url, media.uri))

                                file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.Disney+.{media.language}.srt'
                                print(f"下載：{file_name}")
                                for segement in re.findall(r'.+\-MAIN\/.+\.vtt', m3u_sub.dumps()):
                                    segement_url = os.path.join(
                                        f'{base_url}/r/', segement)
                                    # print(segement_url)
                                    if media.language == 'zh-Hant':
                                        os.makedirs(os.path.dirname(
                                            tmp_folder_path + '/'), exist_ok=True)
                                        download_file(segement_url, os.path.join(
                                            tmp_folder_path, os.path.basename(segement_url)))
                                    elif media.language == 'en':
                                        os.makedirs(os.path.dirname(
                                            en_tmp_folder_path + '/'), exist_ok=True)
                                        download_file(segement_url, os.path.join(
                                            en_tmp_folder_path, os.path.basename(segement_url)))
                                    elif media.language == 'zh-HK':
                                        os.makedirs(os.path.dirname(
                                            hk_tmp_folder_path + '/'), exist_ok=True)
                                        download_file(segement_url, os.path.join(
                                            hk_tmp_folder_path, os.path.basename(segement_url)))

                                print()
                                if media.language == 'zh-Hant':
                                    convert_subtitle(tmp_folder_path)
                                    merge_subtitle(tmp_folder_path, file_name)
                                elif media.language == 'en':
                                    convert_subtitle(en_tmp_folder_path)
                                    merge_subtitle(
                                        en_tmp_folder_path, file_name)
                                elif media.language == 'zh-HK':
                                    convert_subtitle(hk_tmp_folder_path)
                                    merge_subtitle(
                                        hk_tmp_folder_path, file_name)

            print(folder_path)
            convert_subtitle(folder_path, 'disney')
        driver.quit()
