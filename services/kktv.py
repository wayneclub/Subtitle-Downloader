"""
This module is to download subtitle from KKTV
"""

import json
import re
import shutil
import os
from bs4 import BeautifulSoup
from common.utils import check_url_exist, download_file, convert_subtitle


def download_subtitle(driver, output, drama_id, download_season, last_episode):
    """Download subtitle from KKTV"""
    web_content = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()
    try:

        data = json.loads(web_content.find(
            'script', id='__NEXT_DATA__').string)

        drama = data['props']['initialState']['titles']['byId'][drama_id]

        if drama:
            if 'title' in drama:
                drama_name = drama['title']

            if 'titleType' in drama and drama['titleType'] == 'film':
                film = True
            else:
                film = False

            anime = False
            if 'genres' in drama:
                for genre in drama['genres']:
                    if 'title' in genre and genre['title'] == '動漫':
                        anime = True

            if 'totalSeriesCount' in drama:
                season_num = drama['totalSeriesCount']

            if film or anime:
                print(drama_name)
            else:
                if 'dual_subtitle' in drama['contentLabels']:
                    print(f"{drama_name} 共有：{season_num}季（有提供雙語字幕）")
                else:
                    print(f"{drama_name} 共有：{season_num}季")

            if 'series' in drama:
                for season in drama['series']:
                    season_index = int(season['title'][1])
                    if not download_season or season_index == download_season:
                        season_name = str(season_index).zfill(2)
                        episode_num = len(season['episodes'])

                        folder_path = output

                        if film:
                            print(
                                "\n下載電影\n---------------------------------------------------------------")
                        elif last_episode:
                            print(
                                f"\n第 {season_index} 季 共有：{episode_num} 集\t下載第 {season_index} 季 最後一集\n---------------------------------------------------------------")

                            season['episodes'] = [list(season['episodes'])[-1]]
                        elif anime:
                            folder_path = os.path.join(output, drama_name)
                            print(
                                f"\n共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")
                        else:
                            print(
                                f"\n第 {season_index} 季 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")
                            folder_path = os.path.join(
                                output, f'{drama_name}.S{season_name}')
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)

                        jp_lang = False
                        ko_lang = False
                        for episode in season['episodes']:
                            episode_index = int(
                                episode['id'].replace(episode['seriesId'], ''))
                            if len(season['episodes']) < 100:
                                episode_name = str(episode_index).zfill(2)
                            else:
                                episode_name = str(episode_index).zfill(3)

                            if not episode['subtitles']:
                                print("\n無提供可下載的字幕\n")
                                exit()
                            if 'ja' in episode['subtitles']:
                                jp_lang = True
                            if 'ko' in episode['subtitles']:
                                ko_lang = True

                            episode_uri = episode['mezzanines']['dash']['uri']
                            if episode_uri:
                                episode_link_search = re.search(
                                    r'https:\/\/theater\.kktv\.com\.tw([^"]+)_dash\.mpd', episode_uri)
                                if episode_link_search:
                                    episode_link = episode_link_search.group(
                                        1)
                                    epsiode_search = re.search(
                                        drama_id + '[0-9]{2}([0-9]{4})_', episode_uri)
                                    if epsiode_search:
                                        subtitle_link = f'https://theater-kktv.cdn.hinet.net{episode_link}_sub/zh-Hant.vtt'

                                        ja_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ja.vtt')

                                        ko_subtitle_link = subtitle_link.replace(
                                            'zh-Hant.vtt', 'ko.vtt')

                                        if film:
                                            file_name = f'{drama_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                        elif anime:
                                            file_name = f'{drama_name}E{episode_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                        else:
                                            file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.KKTV.zh-Hant.vtt'
                                            ja_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ja.vtt')
                                            ko_file_name = file_name.replace(
                                                'zh-Hant.vtt', 'ko.vtt')

                                            ja_folder_path = os.path.join(
                                                folder_path, '日語')
                                            ko_folder_path = os.path.join(
                                                folder_path, '韓語')

                                        os.makedirs(
                                            folder_path, exist_ok=True)

                                        if jp_lang:
                                            os.makedirs(
                                                ja_folder_path, exist_ok=True)

                                        if ko_lang:
                                            os.makedirs(
                                                ko_folder_path, exist_ok=True)

                                        download_file(subtitle_link, os.path.join(
                                            folder_path, os.path.basename(file_name)))

                                        if jp_lang and check_url_exist(ja_subtitle_link):
                                            download_file(ja_subtitle_link, os.path.join(
                                                ja_folder_path, os.path.basename(ja_file_name)))

                                        if ko_lang and check_url_exist(ko_subtitle_link):
                                            download_file(ko_subtitle_link, os.path.join(
                                                ko_folder_path, os.path.basename(ko_file_name)))

                        print()
                        if film or last_episode:
                            convert_subtitle(os.path.join(
                                folder_path, file_name))
                        else:
                            if jp_lang:
                                convert_subtitle(ja_folder_path)
                            if ko_lang:
                                convert_subtitle(ko_folder_path)

                            convert_subtitle(folder_path, 'kktv')

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")
