"""
This module is to download subtitle from KKTV
"""

import json
import re
import shutil
import os
from bs4 import BeautifulSoup
from common.utils import check_url_exist, download_file, convert_subtitle


def download_subtitle(driver, output, drama_id, download_season, download_episode, last_episode, from_season, from_episode):
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
                if download_season and not film and not anime:
                    if int(download_season) > season_num:
                        print(
                            f"\n該劇只有{season_num}季，沒有第 {download_season} 季")
                        exit()
                    season_start = int(download_season)-1
                    season_end = int(download_season)
                elif last_episode and not film and not anime:
                    season_start = season_num-1
                    season_end = season_num
                elif from_season and not film and not anime:
                    if int(from_season) > season_num:
                        print(f"\n該劇只有{season_num}季，沒有第 {from_season} 季")
                        exit()
                    season_start = int(from_season)-1
                    season_end = season_num
                else:
                    season_start = 0
                    season_end = season_num

                for series in drama['series'][season_start:season_end]:
                    if 'title' in series:
                        series_title = series['title']
                    if 'id' in series:
                        season_search = re.search(
                            drama_id + '([0-9]{2})', series['id'])
                        if season_search:
                            season_name = season_search.group(1)

                    if 'episodes' in series:
                        episode_num = len(series['episodes'])

                        folder_path = output

                        if film:
                            episode_start = 0
                            episode_end = episode_num
                            print(
                                "\n下載電影\n---------------------------------------------------------------")
                        elif anime:
                            folder_path = output + drama_name
                            episode_start = 0
                            episode_end = episode_num
                            print(
                                f"\n共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")
                        elif download_episode:
                            if int(download_episode) > episode_num:
                                print(
                                    f"\n該劇只有{episode_num}集，沒有第 {download_episode} 集")
                                exit()

                            episode_start = int(download_episode)-1
                            episode_end = int(download_episode)

                            print(
                                f"\n{series_title} 共有：{episode_num} 集\t下載第 {download_season} 季 第{str(episode_end).zfill(2)}集\n---------------------------------------------------------------")
                        elif last_episode:
                            episode_start = episode_num-1
                            episode_end = episode_num

                            if download_season:
                                print(
                                    f"\n{series_title} 共有：{episode_num} 集\t下載第 {download_season} 季 最後一集\n---------------------------------------------------------------")
                            else:
                                print(
                                    f"\n{series_title} 共有：{episode_num} 集\t下載第 {str(season_num).zfill(2)} 季 最後一集\n---------------------------------------------------------------")
                        elif from_episode:
                            if int(from_episode) > episode_num:
                                print(
                                    f"\n該劇只有{episode_num}集，沒有第 {from_episode} 集")
                                exit()
                            folder_path = f'{output + drama_name}.S{season_name}'
                            if os.path.exists(folder_path):
                                shutil.rmtree(folder_path)

                            episode_start = int(from_episode)-1
                            episode_end = episode_num

                            print(
                                f"\n{series_title} 共有：{episode_num} 集\t下載第{str(from_season).zfill(2)}季 第{str(from_episode).zfill(2)}集 至 最後一集\n---------------------------------------------------------------")
                        else:
                            folder_path = f'{output + drama_name}.S{season_name}'
                            episode_start = 0
                            episode_end = episode_num
                            print(
                                f"\n{series_title} 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")

                        jp_lang = False
                        ko_lang = False
                        for episode in series['episodes'][episode_start:episode_end]:
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
                                    episode_link = episode_link_search.group(1)
                                    epsiode_search = re.search(
                                        drama_id + '[0-9]{2}([0-9]{4})_', episode_uri)
                                    if epsiode_search:
                                        episode_name = epsiode_search.group(
                                            1)[-2:]
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

                                        if not download_episode:
                                            os.makedirs(os.path.dirname(
                                                f'{folder_path}/'), exist_ok=True)

                                            if jp_lang:
                                                os.makedirs(os.path.dirname(
                                                    f'{ja_folder_path}/'), exist_ok=True)

                                            if ko_lang:
                                                os.makedirs(os.path.dirname(
                                                    f'{ko_folder_path}/'), exist_ok=True)

                                        download_file(subtitle_link, os.path.join(
                                            folder_path, os.path.basename(file_name)))

                                        if jp_lang and check_url_exist(ja_subtitle_link):
                                            download_file(ja_subtitle_link, os.path.join(
                                                ja_folder_path, os.path.basename(ja_file_name)))

                                        if ko_lang and check_url_exist(ko_subtitle_link):
                                            download_file(ko_subtitle_link, os.path.join(
                                                ko_folder_path, os.path.basename(ko_file_name)))

                        print()
                        if download_episode or last_episode or film:
                            convert_subtitle(folder_path + file_name)
                        else:
                            if jp_lang:
                                convert_subtitle(ja_folder_path)
                            if ko_lang:
                                convert_subtitle(ko_folder_path)

                            convert_subtitle(folder_path, 'kktv')

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")
