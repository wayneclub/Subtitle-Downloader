import os
import json
import shutil
from urllib.parse import urlparse
from typing import List
from pathlib import Path
from datetime import datetime
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.models.base import BaseUri
from tools.XstreamDL_CLI.models.key import StreamKey
from tools.XstreamDL_CLI.models.segment import Segment
from tools.XstreamDL_CLI.util.texts import t_msg
from tools.XstreamDL_CLI.util.concat import Concat
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class Stream:
    '''
    自适应流具体实现的父类
    每一条流应当具有以下基本属性：
        - 名称
        - 分段链接列表
        - 分辨率
        - 码率
        - 时长
        - 编码
        - 语言
    具有以下函数
        - 扩展分段 某些情况下需要合并两或多条流
        - 计算全部分段时长和大小
        - 显示流信息 总时长和大小
        - 从第一个分段读取流信息
        - 保存流相关信息至本地
        - 增加分段
        - 增加密钥信息
        - 合并 一般在下载完成之后
    '''

    def __init__(self, index: int, uri_item: BaseUri, save_dir: Path):
        self.index = index
        self.name = uri_item.name
        self.home_url = uri_item.home_url
        self.base_url = uri_item.base_url.rstrip('/')
        self.save_dir = save_dir / self.name
        self.segments = []  # type: List[Segment]
        self.duration = 0.0
        self.filesize = 0
        self.lang = ''
        self.bandwidth = None  # type: int
        self.fps = None  # type: int
        self.resolution = ''  # type: str
        self.codecs = None  # type: str
        self.streamkeys = []  # type: List[StreamKey]
        # 初始化默认设定流类型
        self.stream_type = ''  # type: str
        self.model = ''
        self.suffix = '.mp4'

    def segments_extend(self, segments: List[Segment], has_init: bool = False, name_from_url: bool = False):
        '''
        某些情况下对流进行合并
        需要更新一下新增分段的文件名
        '''
        offset = len(self.segments)
        _segments = []
        for segment in segments:
            # 跳过init分段
            if segment.index == -1:
                continue
            segment.add_offset_for_name(
                offset, has_init, name_from_url=name_from_url)
            _segments.append(segment)
        self.segments.extend(_segments)

    def live_segments_extend(self, segments: List[Segment], has_init: bool, name_from_url: bool = False, compare_with_url: bool = False):
        '''
        对live流进行合并
        - 更新新增分段的文件名
        - 根据链接中的path部分检查是不是重复了
        '''
        if compare_with_url:
            url_paths = [
                segment.url for segment in self.segments if segment.skip_concat is False]
        else:
            url_paths = [urlparse(
                segment.url).path for segment in self.segments if segment.skip_concat is False]
        offset = len(self.segments)
        _segments = []
        for segment in segments:
            if segment.index == -1:
                continue
            if compare_with_url:
                _url = segment.url
            else:
                _url = urlparse(segment.url).path
            if _url in url_paths:
                continue
            segment.set_offset_for_name(
                offset, has_init, name_from_url=name_from_url)
            offset += 1
            _segments.append(segment)
        self.segments.extend(_segments)

    def calc(self):
        self.duration = sum(
            [segment.duration for segment in self.segments if segment.skip_concat is False])
        self.filesize = sum(
            [segment.filesize for segment in self.segments if segment.skip_concat is False])
        self.filesize = self.filesize / 1024 / 1024

    def get_name(self):
        return self.name

    def get_stream_model(self):
        assert self.model != '', 'report this content to me'
        return self.model

    def check_record_time(self, live_duration: float):
        # 修正calc计算后 直接比较当前流的 duration 即可
        if live_duration == 0.0:
            return False
        return self.duration >= live_duration

    def get_init_msg(self, show_init: bool = False):
        if show_init is False:
            return ''
        for _ in self.segments:
            if _.segment_type == 'init':
                return ' initialization -> ' + _.url.split('?')[0].split('/')[-1]
        return ''

    def fix_name(self, index: int, index_to_name: bool = False):
        if index_to_name:
            self.name = f'{index}_{self.name}'

    def show_info(self, index: int, show_init: bool = False, index_to_name: bool = False):
        ''' 显示信息 '''
        self.calc()
        self.fix_name(index, index_to_name)
        if self.filesize > 0:
            print(
                f'{index:>3} {t_msg.total_segments_info_1} {len(self.segments):>4} {t_msg.total_segments_info_2} '
                f'{self.duration:>7.2f}s {self.filesize:.2f}MiB {self.get_name()}{self.get_init_msg(show_init)}'
            )
        else:
            print(
                f'{index:>3} {t_msg.total_segments_info_1} {len(self.segments):>4} {t_msg.total_segments_info_2} '
                f'{self.duration:>7.2f}s {self.get_name()}{self.get_init_msg(show_init)}'
            )

    def read_stream_header(self):
        ''' 读取一部分数据 获取流的信息 '''
        pass

    def show_segments(self):
        for segment in self.segments:
            print(segment.url)

    def dump_segments(self):
        self.calc()
        ''' 保存分段信息 '''
        self.save_dir = self.save_dir.parent / self.get_name()
        if self.save_dir.exists() is False:
            self.save_dir.mkdir()
        keys = []
        if len(self.streamkeys) > 0:
            for streamkey in self.streamkeys:
                keys.append(streamkey.dump())
        info = {
            'name': self.get_name(),
            'path': self.save_dir.resolve().as_posix(),
            'creatTime': f'{datetime.now()}',
            'key': keys,
            'segments': [],
        }
        for segment in self.segments:
            segment.folder = self.save_dir
            info['segments'].append(
                {
                    'url': segment.url,
                    'size': segment.filesize,
                    'byterange': segment.byterange,
                    'name': segment.name,
                }
            )
        data = json.dumps(info, ensure_ascii=False, indent=4)
        (self.save_dir / 'raw.json').write_text(data, encoding='utf-8')

    def append_segment(self):
        ''' 新增分段 '''
        pass

    def append_key(self, streamkey: StreamKey):
        ''' 新增key '''
        self.streamkeys.append(streamkey)

    def fix_url(self, url: str) -> str:
        if url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://'):
            return url
        elif url.startswith('/'):
            return f'{self.home_url}{url}'
        elif url.startswith('../'):
            fixed_base_url = '/'.join(self.base_url.split("/")[:-1])
            return f'{fixed_base_url}{url[2:]}'
        else:
            return f'{self.base_url}/{url}'

    def concat(self, args: CmdArgs):
        ''' 合并视频 '''
        out = Path(self.save_dir.absolute().as_posix() + self.suffix)
        if args.overwrite is False and out.exists() is True:
            logger.info(
                f'{t_msg.try_to_concat} {self.get_name()} {t_msg.cancel_concat_reason_1}')
            return True
        skip_count = 0
        names = []
        for segment in self.segments:
            if segment.skip_concat:
                skip_count += 1
                continue
            segment_path = self.save_dir / segment.name
            if segment_path.exists() is False:
                continue
            names.append(segment.name)
        # 仅在非直播时这样比较
        if args.live is False and len(names) != len(self.segments) - skip_count:
            logger.error(
                f'{t_msg.try_to_concat} {self.get_name()} {t_msg.cancel_concat_reason_2}')
            return False
        if hasattr(self, "xkey") and self.xkey is not None and self.xkey.method.upper() in ['SAMPLE-AES', 'SAMPLE-AES-CTR']:
            logger.warning(t_msg.force_use_raw_concat_for_sample_aes)
            args.raw_concat = True
        if len(self.streamkeys) > 0:
            args.raw_concat = True
        ori_path = os.getcwd()
        # 需要在切换目录前获取
        os.chdir(self.save_dir.absolute().as_posix())
        cmds, _outs = Concat.gen_cmds_outs(out, names, args)
        if len(cmds) > 0 and Path(args.ffmpeg).exists() is False:
            logger.warning(
                'ffmpeg is not exists, please put ffmpeg to binaries folder')
        for cmd in cmds:
            os.system(cmd)
        # 执行完合并命令后即刻返回原目录
        os.chdir(ori_path)
        # 合并成功则根据设定删除临时文件
        if out.exists():
            logger.info(f'{out.as_posix()} was merged successfully')
            if args.enable_auto_delete:
                shutil.rmtree(self.save_dir.absolute().as_posix())
                logger.info(
                    f'{self.save_dir.absolute().as_posix()} was deleted')
        else:
            logger.warning(f'merge {out.as_posix()} failed')
        # 针对DASH流 如果有key 那么就解密 注意 HLS是边下边解密
        # 加密文件合并输出和临时文件夹同一级 所以前面的删除动作并不影响进一步解密
        if args.key is not None:
            if Path(args.mp4decrypt).exists() is False:
                logger.warning(
                    'mp4decrypt is not exists, please put mp4decrypt to binaries folder')
            Concat.call_mp4decrypt(out, args)
        if args.enable_auto_delete and self.save_dir.exists():
            shutil.rmtree(self.save_dir.absolute().as_posix())
        return True

    def fix_header(self, is_fake: bool):
        pass
