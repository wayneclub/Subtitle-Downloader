"""
This module is to download subtitle from Friday影音
"""

import json
import re
import shutil
import os
from bs4 import BeautifulSoup
from common.utils import get_season_number, check_url_exist, download_file, convert_subtitle


def download_subtitle(driver, output, genre, download_season, download_episode, last_episode, from_season, from_episode):
    """Download subtitle from friDay"""
    web_content = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()
    try:

        title = web_content.find('h1', class_='title-chi')
        if title:
            if genre == 'movie':
                drama_name = title.text
                print(drama_name)
            else:
                season_search = re.search(
                    r'(.+?)第(.+?)季', title.text)
                if season_search:
                    drama_name = season_search.group(1).strip()
                    season_name = get_season_number(season_search.group(2))
                else:
                    drama_name = title.text.strip()
                    season_name = '01'

        drama = web_content.find('ul', class_='episode-container')
        if drama:
            episode_num = len(drama.findAll('li'))
            folder_path = output

            episode_list = []
            season_set = set()
            for ep in drama.findAll('p'):
                season_search = re.search(r'第(.+?)季(.+)', ep.text)
                if season_search:
                    season_name = get_season_number(season_search.group(1))
                    season_set.add(season_name)
                    episode_name = f'S{season_name}E{season_search.group(2)}'
                else:
                    season_set.add(season_name)
                    episode_name = f'S{season_name}E{(ep.text).zfill(2)}'
                episode_list.append(episode_name)

            season_num = len(season_set)
            if season_num > 1:
                print(f"{drama_name} 共有：{season_num}季")
            else:
                print(f"{drama_name} 第{season_name}季")

            episode_list_start = episode_list[0]
            episode_list_end = episode_list[-1]

            if download_season and download_season not in season_set:
                print(f"\n該劇只有第 {season_name} 季，沒有第 {download_season} 季")
                exit(1)

            if from_season and from_season not in season_set:
                print(f"\n該劇只有第 {season_name} 季，沒有第 {from_season} 季")
                exit()

            if download_episode:
                if f'S{download_season}E{download_episode}' not in episode_list:
                    print(
                        f"\n該劇只有從 {episode_list_start} - {episode_list_end}，沒有第{ download_season }季 第 {download_episode} 集\n---------------------------------------------------------------")
                    exit(1)

                episode_start = episode_list.index(
                    f'S{download_season}E{download_episode}')
                episode_end = episode_list.index(
                    f'S{download_season}E{download_episode}') + 1
                print(
                    f"\n第 {download_season} 季 共有：{str(len([s for s in episode_list if 'S' + download_season in s]))} 集\t下載第 {download_season} 季 第 {download_episode} 集\n---------------------------------------------------------------")
            elif last_episode:
                episode_start = episode_num-1
                episode_end = episode_num
                print(
                    f"\n第 {season_name} 季 共有：{str(len([s for s in episode_list if 'S' + season_name in s]))} 集\t下載第 {season_name.zfill(2)} 季 最後一集\n---------------------------------------------------------------")
            elif from_episode:
                if f'S{from_season}E{from_episode}' not in episode_list:
                    print(
                        f"\n該劇只有從 {episode_list_start} - {episode_list_end}，沒有第 {from_season} 季 第 {from_episode} 集\n---------------------------------------------------------------")
                    exit(1)

                folder_path = os.path.join(
                    output, f'{drama_name}.S{season_name}')
                episode_start = int(from_episode)-1
                episode_end = episode_num
                print(
                    f"\n第 {from_season} 季 共有：{str(len([s for s in episode_list if 'S' + from_season in s]))} 集\t下載第 {from_season} 季 第 {from_episode} 集\n---------------------------------------------------------------")
            else:
                if season_num > 1:
                    folder_path = os.path.join(output, drama_name)
                else:
                    folder_path = os.path.join(
                        output, f'{drama_name}.S{season_name}')
                episode_start = 0
                episode_end = episode_num
                if re.search(r'S\d+E01', episode_list[0]):
                    print(
                        f"\n共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")
                else:
                    print(
                        f"\n第 {season_name} 季 共有：{episode_list[0].split('E')[1]}-{episode_list[-1].split('E')[1]} 集\t下載全集\n---------------------------------------------------------------")

            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            jp_lang = False
            dual_lang = False
            for episode in drama.findAll('li')[episode_start:episode_end]:

                sub_search = re.search(
                    r'\?sid=(.+?)&.+?&epi=(.+?)&.+', episode['data-src'])
                if sub_search:
                    subtitle_link = f'https://sub.video.friday.tw/{sub_search.group(1)}.cht.vtt'

                    subtitle_link_2 = subtitle_link.replace(
                        '.cht.vtt', '_80000000_ffffffff.cht.vtt')
                    subtitle_link_3 = subtitle_link.replace(
                        '.cht.vtt', '_ff000000_ffffffff.cht.vtt')

                    season_search = re.search(
                        r'第(.+?)季(.+)', sub_search.group(2))
                    if season_search:
                        season_name = get_season_number(season_search.group(1))
                        episode_name = season_search.group(2)
                    else:
                        episode_name = sub_search.group(2).zfill(2)

                    file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.friDay.zh-Hant.vtt'

                    ja_file_name = file_name.replace('.zh-Hant.vtt', '.ja.vtt')
                    dual_file_name = file_name.replace('.zh-Hant.vtt', '.vtt')
                    ja_folder_path = os.path.join(folder_path, '日語')
                    dual_folder_path = os.path.join(folder_path, '雙語')

                    if check_url_exist(subtitle_link):
                        ja_subtitle_link = get_ja_subtitle_link(
                            subtitle_link)
                        dual_subtitle_link = get_dual_subtitle_link(
                            subtitle_link)
                        if check_url_exist(ja_subtitle_link):
                            jp_lang = True
                        if check_url_exist(dual_subtitle_link):
                            dual_lang = True
                    elif check_url_exist(subtitle_link_2):
                        subtitle_link = subtitle_link_2
                        ja_subtitle_link = get_ja_subtitle_link(
                            subtitle_link)
                        dual_subtitle_link = get_dual_subtitle_link(
                            subtitle_link)
                        if check_url_exist(get_ja_subtitle_link(subtitle_link)):
                            jp_lang = True
                        if check_url_exist(get_dual_subtitle_link(subtitle_link)):
                            dual_lang = True
                    elif check_url_exist(subtitle_link_3):
                        subtitle_link = subtitle_link_3
                        ja_subtitle_link = get_ja_subtitle_link(
                            subtitle_link)
                        dual_subtitle_link = get_dual_subtitle_link(
                            subtitle_link)
                        if check_url_exist(get_ja_subtitle_link(subtitle_link)):
                            jp_lang = True
                        if check_url_exist(get_dual_subtitle_link(subtitle_link)):
                            dual_lang = True
                    else:
                        print("抱歉，此劇只有硬字幕，可去其他串流平台查看")
                        exit(0)

                    if jp_lang and episode_name == 1:
                        print("（有提供日語字幕）")

                    if dual_lang and episode_name == 1:
                        print("（有提供雙語字幕）")

                    if not download_episode:
                        os.makedirs(folder_path, exist_ok=True)

                        if jp_lang:
                            os.makedirs(ja_folder_path, exist_ok=True)
                        if dual_lang:
                            os.makedirs(dual_folder_path, exist_ok=True)

                    download_file(subtitle_link, os.path.join(
                        folder_path, file_name))

                    if jp_lang:
                        download_file(ja_subtitle_link, os.path.join(
                            ja_folder_path, ja_file_name))
                    if dual_lang:
                        download_file(dual_subtitle_link, os.path.join(
                            dual_folder_path, dual_file_name))
            print()
            if download_episode or last_episode:
                convert_subtitle(folder_path + file_name)
            else:
                if jp_lang:
                    convert_subtitle(ja_folder_path)
                if dual_lang:
                    convert_subtitle(dual_folder_path)

                convert_subtitle(folder_path, 'friday')

        if genre == 'movie':
            sid_search = web_content.find(
                'div', class_='popup-video-container content-vod')
            if sid_search:
                sub_search = re.search(
                    r'\/player\?sid=(.+?)&stype=.+', sid_search['data-src'])
                if sub_search:

                    subtitle_link = f'https://sub.video.friday.tw/{sub_search.group(1)}.cht.vtt'

                    file_name = f'{drama_name}.WEB-DL.friDay.zh-Hant.vtt'

                    folder_path = output

                    if check_url_exist(subtitle_link):
                        if not download_episode:
                            os.makedirs(folder_path, exist_ok=True)

                        download_file(subtitle_link, os.path.join(
                            folder_path, file_name))
                        convert_subtitle(os.path.join(folder_path, file_name))
                    else:
                        print("找不到外掛字幕，請去其他平台尋找")
                        exit()

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")


def get_ja_subtitle_link(subtitle_link):
    return subtitle_link.replace('.cht.vtt', '.jpn.vtt')


def get_dual_subtitle_link(subtitle_link):
    return subtitle_link.replace('.cht.vtt', '.deu.vtt')
