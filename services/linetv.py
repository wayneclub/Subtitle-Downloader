"""
This module is to download subtitle from LineTV
"""

import json
import re
import shutil
import os
from urllib.parse import quote
from time import strftime, localtime
from common.utils import check_url_exist, download_file, convert_subtitle
from common.dictionary import convert_chinese_number


def download_subtitle(web_content, output, drama_id, last_episode):
    """Download subtitle from LineTV"""

    try:
        if web_content.find('script') and web_content.find('script').string:
            data = json.loads(web_content.find('script').string.replace(
                'window.__INITIAL_STATE__ = ', ''))

            drama = data['entities']['dramaInfo']['byId'][drama_id]

            if drama:
                if 'drama_name' in drama:
                    season_search = re.search(
                        r'(.+?)第(.+?)季', drama['drama_name'])
                    if season_search:
                        drama_name = season_search.group(1).strip()
                        season_name = convert_chinese_number(
                            season_search.group(2))
                    else:
                        drama_name = drama['drama_name'].strip()
                        season_name = '01'

                    print(f"{drama_name} 第 {int(season_name)} 季")

                if 'current_eps' in drama:
                    episode_num = drama['current_eps']
                    folder_path = output

                    if last_episode:
                        drama['eps_info'] = [list(drama['eps_info'])[-1]]

                        print(
                            f"\n第 {int(season_name)} 季 共有：{episode_num} 集\t下載第 {int(season_name)} 季 最後一集\n---------------------------------------------------------------")
                    else:
                        folder_path = os.path.join(
                            output, f'{drama_name}.S{season_name}')
                        if drama['current_eps'] != drama['total_eps']:
                            print(
                                f"\n第 {int(season_name)} 季 共有：{drama['total_eps']} 集\t更新至 第 {episode_num} 集\t下載全集\n---------------------------------------------------------------")
                        else:
                            print(
                                f"\n第 {int(season_name)} 季 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")

                        if os.path.exists(folder_path):
                            shutil.rmtree(folder_path)

                    if 'eps_info' in drama:
                        for episode in drama['eps_info']:
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

                                if not last_episode:
                                    os.makedirs(folder_path, exist_ok=True)

                                download_file(subtitle_link, os.path.join(
                                    folder_path, file_name))

                        if last_episode:
                            convert_subtitle(os.path.join(
                                folder_path, file_name))
                        else:
                            convert_subtitle(folder_path, 'linetv')

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")
