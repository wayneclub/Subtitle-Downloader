"""
This module is to download subtitle from LineTV
"""

import json
import re
import shutil
import os
from urllib.parse import quote
from time import strftime, localtime
from common.utils import get_season_number, check_url_exist, download_file, convert_subtitle


def download_subtitle(web_content, output, drama_id, download_season, download_episode, last_episode, from_season, from_episode):
    """Download subtitle from LineTV"""

    try:
        if web_content.find('script') and web_content.find('script').string:
            data = json.loads(web_content.find('script').string.replace(
                'window.__INITIAL_STATE__ = ', ''))

            drama = data['entities']['dramaInfo']['byId'][drama_id]

            if drama:
                if 'drama_name' in drama:
                    season_search = re.search(
                        r'.+?第(.+?)季', drama['drama_name'])
                    if season_search:
                        drama_name = (
                            drama['drama_name'].split('第')[0]).strip()
                        season_name = get_season_number(season_search.group(1))
                    else:
                        drama_name = drama['drama_name'].strip()
                        season_name = '01'

                    print(f"{drama_name} 第 {season_name} 季")

                if download_season and int(download_season) != int(season_name):
                    print(
                        f"\n該劇只有第{int(season_name)}季，沒有第 {download_season} 季")
                    exit()

                if from_season and int(from_season) != int(season_name):
                    print(f"\n該劇只有第{int(season_name)}季，沒有第 {from_season} 季")
                    exit()

                if 'current_eps' in drama:
                    episode_num = drama['current_eps']
                    folder_path = output

                    if download_episode:
                        if int(download_episode) > episode_num:
                            print(
                                f"\n該劇只有{episode_num}集，沒有第 {download_episode} 集")
                            exit()
                        episode_start = int(download_episode)-1
                        episode_end = int(download_episode)
                        print(
                            f"\n第 {season_name} 季 共有：{episode_num} 集\t下載第 {download_season} 季 第 {str(episode_end).zfill(2)} 集\n---------------------------------------------------------------")
                    elif last_episode:
                        episode_start = episode_num-1
                        episode_end = episode_num

                        # for episode in reversed(drama['eps_info']):
                        #     if episode['free_date']:
                        #         free_date = time.localtime(
                        #             int(episode['free_date'])/1000)
                        #         if free_date < time.localtime():
                        #             episode_start = episode['number']-1
                        #             episode_end = episode['number']
                        #             break

                        print(
                            f"\n第 {season_name} 季 共有：{episode_num} 集\t下載第{season_name.zfill(2)}季 最後一集\n---------------------------------------------------------------")
                    elif from_episode:
                        if int(from_episode) > episode_num:
                            print(
                                f"\n該劇只有{episode_num}集，沒有第 {from_episode} 集")
                            exit()
                        folder_path = os.path.join(
                            output, f'{drama_name}.S{season_name}')
                        episode_start = int(from_episode)-1
                        episode_end = episode_num
                        print(
                            f"\n第 {season_name} 季 共有：{episode_num} 集\t下載第 {from_season} 季 第 {from_episode} 集 至 最後一集\n---------------------------------------------------------------")
                    else:
                        folder_path = os.path.join(
                            output, f'{drama_name}.S{season_name}')
                        episode_start = 0
                        episode_end = episode_num
                        if drama['current_eps'] != drama['total_eps']:
                            print(
                                f"\n第 {season_name} 季 共有：{drama['total_eps']} 集\t更新至 第 {episode_num} 集\t下載全集\n---------------------------------------------------------------")
                        else:
                            print(
                                f"\n第 {season_name} 季 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")

                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)

                    if 'eps_info' in drama:
                        for episode in drama['eps_info'][episode_start: episode_end]:
                            if 'number' in episode:
                                episode_name = str(episode['number'])
                                subtitle_link = f'https://s3-ap-northeast-1.amazonaws.com/tv-aws-media-convert-input-tokyo/subtitles/{drama_id}/{drama_id}-eps-{episode_name}.vtt'

                                file_name = f'{drama_name}.S{season_name}E{episode_name.zfill(2)}.WEB-DL.LineTV.zh-Hant.vtt'

                                if not check_url_exist(subtitle_link):
                                    if check_url_exist(subtitle_link.replace('tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')):
                                        subtitle_link = subtitle_link.replace(
                                            'tv-aws-media-convert-input-tokyo', 'aws-elastic-transcoder-input-tokyo')
                                    else:
                                        subtitle_link = f'https://choco-tv.s3.amazonaws.com/subtitle/{drama_id}-{quote(drama_name.encode("utf8"))}/{drama_id}-eps-{episode_name}.vtt'
                                        if not check_url_exist(subtitle_link):
                                            if episode['free_date']:
                                                free_date = strftime(
                                                    '%Y-%m-%d', localtime(int(episode['free_date'])/1000))
                                                print(
                                                    f"{file_name}\t...一般用戶於{free_date}開啟")

                                if not download_episode:
                                    os.makedirs(folder_path, exist_ok=True)

                                download_file(subtitle_link, os.path.join(
                                    folder_path, file_name))

                        if download_episode or last_episode:
                            convert_subtitle(folder_path + file_name)
                        else:
                            convert_subtitle(folder_path, 'linetv')

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")
