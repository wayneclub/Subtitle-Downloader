import sys
import math
import time
import signal
import asyncio
import binascii
from logging import Logger
from typing import List, Set, Dict
from asyncio import new_event_loop
from asyncio import AbstractEventLoop, Future, Task
from aiohttp import ClientSession, ClientResponse, TCPConnector, client_exceptions
from aiohttp_socks import ProxyConnector
from concurrent.futures._base import TimeoutError, CancelledError
from tools.xstream.cmdargs import CmdArgs
from tools.xstream.models.stream import Stream
from tools.xstream.models.segment import Segment
from tools.xstream.util.decryptors.aes import CommonAES
from tools.xstream.util.texts import t_msg


def auto_choose_resolution(args: CmdArgs, streams: List[Stream]) -> List[Stream]:
    target_indexes = []
    for index, stream in enumerate(streams):
        # 跳过非目标类型
        if stream.stream_type != 'video':
            continue
        # 如果当前流的目标分辨率与预设分辨率不匹配 跳过
        if stream.resolution.split('x')[1] != args.resolution:
            continue
        target_indexes.append(index)
    return target_indexes


def auto_choose_best_streams(args: CmdArgs, streams: List[Stream]) -> List[Stream]:
    def choose_best_stream_by_type(target_type: str):
        ''' return target index '''
        target_stream = None
        for stream in streams:
            # 跳过非目标类型
            if stream.stream_type != target_type:
                continue
            # 跳过没有bandwidth的流
            if not stream.bandwidth:
                continue
            # 目标是视频并且下载选项设定了目标分辨率
            if target_type == 'video' and args.resolution != '':
                # 如果当前流的目标分辨率与预设分辨率不匹配 跳过
                if stream.resolution.split('x')[1] != args.resolution:
                    continue
            # 如果target_stream还没设置 当前流设置为target_stream
            if target_stream is None:
                target_stream = stream
                continue
            # 当前流码率比之前选定的流更高 设置当前流为选择的流
            if stream.bandwidth > target_stream.bandwidth:
                target_stream = stream
        # 在上面的检查中确实设置了流 则返回其索引
        # 这里其实返回流更合理 但是上一级其他位置一直用的索引 所以这里先不改
        if target_stream:
            return streams.index(target_stream)
        # 否则返回None 交由上一级判断
        return target_stream
    best_audio_stream_index = choose_best_stream_by_type('audio')
    best_video_stream_index = choose_best_stream_by_type('video')
    if args.audio_only:
        if best_audio_stream_index is not None:
            return [best_audio_stream_index]
        else:
            return []
    if args.video_only:
        if best_video_stream_index is not None:
            return [best_video_stream_index]
        else:
            return []
    target_streams = []
    if best_audio_stream_index is not None:
        target_streams.append(best_audio_stream_index)
    if best_video_stream_index is not None:
        target_streams.append(best_video_stream_index)
    return target_streams


def get_selected_index(length: int) -> list:
    selected = []
    try:
        text = input(t_msg.input_stream_number).strip()
    except EOFError:
        return []
    if text == '':
        return [index for index in range(length + 1)]
    elif text.isdigit():
        return [int(text)]
    elif '-' in text and len(text.split('-')) == 2:
        start, end = text.split('-')
        if start.strip().isdigit() and end.strip().isdigit():
            return [index for index in range(int(start.strip()), int(end.strip()) + 1)]
    elif text.replace(' ', '').isdigit():
        for index in text.split(' '):
            if index.strip().isdigit():
                if int(index.strip()) <= length:
                    selected.append(int(index))
        return selected
    elif text.replace(',', '').replace(' ', '').isdigit():
        for index in text.split(','):
            if index.strip().isdigit():
                if int(index.strip()) <= length:
                    selected.append(int(index))
        return selected
    return selected


def get_left_segments(stream: Stream):
    count = 0
    completed = 0
    _left_segments = []
    for segment in stream.segments:
        segment_path = segment.get_path()
        if segment_path.exists() is True:
            # 文件落盘 说明下载一定成功了
            if segment_path.stat().st_size == 0:
                segment_path.unlink()
            else:
                count += 1
                completed += segment_path.stat().st_size
                continue
        _left_segments.append(segment)
    return count, completed, _left_segments


def get_connector(args: CmdArgs):
    '''
    connector在一个ClientSession使用后可能就会关闭
    若需要再次使用则需要重新生成
    '''
    if args.proxy != '':
        return ProxyConnector.from_url(
            args.proxy,
            ttl_dns_cache=500,
            ssl=False,
            limit_per_host=args.limit_per_host,
            limit=500,
            force_close=not args.disable_force_close,
            enable_cleanup_closed=not args.disable_force_close
        )
    return TCPConnector(
        ttl_dns_cache=500,
        ssl=False,
        limit_per_host=args.limit_per_host,
        limit=500,
        force_close=not args.disable_force_close,
        enable_cleanup_closed=not args.disable_force_close
    )


class XProgress:

    def __init__(self, title: str, total_count: int, downloaded_count: int, total_size: int, completed_size: int):
        self.last_time = time.time()
        self.title = title
        self.total_count = total_count
        self.downloaded_count = downloaded_count
        self.total_size = total_size
        self.downloaded_size = completed_size
        self.last_size = completed_size
        self.stop = False

    def calc_speed(self, total_size: int, downloaded_size: int):
        ts = time.time()
        tm = ts - self.last_time
        if self.stop is False and tm < 0.3:
            return
        if tm == 0.0:
            return
        speed = (downloaded_size - self.last_size) / tm / 1024 / 1024
        self.last_time = ts
        self.last_size = downloaded_size
        return speed

    def add_downloaded_count(self, downloaded_count: int):
        self.downloaded_count += downloaded_count
        self.update_progress(self.downloaded_count,
                             self.total_size, self.downloaded_size)

    def update_total_size(self, total_size: int):
        self.total_size = total_size
        self.update_progress(self.downloaded_count,
                             self.total_size, self.downloaded_size)

    def decrease_total_count(self):
        self.total_count -= 1
        self.update_progress(self.downloaded_count,
                             self.total_size, self.downloaded_size)

    def add_downloaded_size(self, downloaded_size: int):
        self.downloaded_size += downloaded_size
        self.update_progress(self.downloaded_count,
                             self.total_size, self.downloaded_size)

    def update_progress(self, downloaded_count: int, total_size: int, downloaded_size: int):
        barlen, status = 30, ''
        progress = downloaded_count / self.total_count
        if progress >= 1.0:
            progress, status = 1, '\r\n'
        speed = self.calc_speed(total_size, downloaded_size)
        if speed is None:
            return
        _total_size = total_size / 1024 / 1024
        _downloaded_size = downloaded_size / 1024 / 1024
        bar_str = chr(9608)
        split_str = chr(8226)
        block = int(math.floor(barlen * progress))
        bar = bar_str * block + ' ' * (barlen - block)
        text = (
            f'\r{self.title} {bar} {_downloaded_size:.2f}/{_total_size:.2f}MB {split_str} {speed:.2f}MB/s '
            f'{split_str} {downloaded_count}/{self.total_count} {split_str} {progress * 100:.2f}% {status}'
        )
        sys.stdout.write(text)
        sys.stdout.flush()

    def to_stop(self):
        self.stop = True
        self.update_progress(self.downloaded_count,
                             self.total_size, self.downloaded_size)


class Downloader:

    def __init__(self, logger: Logger, args: CmdArgs):
        self.logger = logger
        self.args = args
        self.xprogress = None  # type: XProgress
        self.terminate = False
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum: int, frame):
        self.logger.debug('stopped by Ctrl C')
        self.terminate = True

    def stop_record(self):
        self.logger.debug('stopped reason: stop_record')
        self.terminate = True

    def do_select(self, streams: List[Stream], selected: list = []):
        if len(selected) > 0:
            return selected
        if streams is None:
            return
        if len(streams) == 0:
            return
        for index, stream in enumerate(streams):
            stream.show_info(index, show_init=self.args.show_init,
                             index_to_name=self.args.index_to_name)
        if self.args.select is True:
            selected = get_selected_index(len(streams))
            if len(selected) == 0:
                self.logger.info(t_msg.select_without_any_stream)
        elif self.args.best_quality:
            selected = auto_choose_best_streams(self.args, streams)
        elif self.args.all_videos:
            selected = [index for index, stream in enumerate(
                streams) if stream.stream_type == 'video']
        elif self.args.all_audios:
            selected = [index for index, stream in enumerate(
                streams) if stream.stream_type == 'audio']
        elif self.args.resolution != '':
            selected = auto_choose_resolution(self.args, streams)
        else:
            selected = [index for index in range(len(streams))]
        if self.args.live is False:
            return selected
        skeys = []
        for select in selected:
            skeys.append(streams[select].get_skey())
        return skeys

    def download_streams(self, streams: List[Stream], selected: list = []):
        selected = self.do_select(streams, selected)
        self.logger.debug(f'selected is {selected}')
        if selected is None:
            return
        should_stop_record = False
        all_results = []
        for index, stream in enumerate(streams):
            if self.terminate is True:
                break
            if self.args.live is False:
                if index not in selected:
                    continue
            else:
                if stream.get_skey() not in selected:
                    continue
            if self.args.live is False and len(stream.segments) == 1:
                self.logger.warning(
                    f'only one segment, download speed maybe slow =>\n{stream.segments[0].url + self.args.url_patch}')
                # continue
            stream.dump_segments()
            max_failed = 5
            if self.args.parse_only:
                if len(stream.segments) <= 5:
                    stream.show_segments()
                continue
            if stream.get_stream_model() == 'mss':
                # 这里的init实际上是不正确的 这里生成是为了满足下载文件检查等逻辑
                stream.fix_header(is_fake=True)
            self.logger.info(f'{stream.get_name()} {t_msg.download_start}.')
            while max_failed > 0:
                loop = new_event_loop()
                results = loop.run_until_complete(
                    self.do_with_progress(loop, stream))
                loop.close()
                all_results.append(results)
                count_none, count_true, count_false = 0, 0, 0
                for _, flag in results.items():
                    if flag is True:
                        count_true += 1
                    elif flag is False:
                        count_false += 1
                    else:
                        count_none += 1
                # 出现False则说明无法下载
                if count_false > 0:
                    break
                # False 0 出现None则说明需要继续下载 否则合并
                if count_none > 0:
                    max_failed -= 1
                    continue
                break
            # track_id 最佳获取方案是从实际分段中提取 通过ism元数据无法直接计算出来
            if stream.get_stream_model() == 'mss':
                stream.fix_header(is_fake=False)
            self.try_concat(stream)
            # 只需要检查一个流的时间达到最大值就停止录制
            # 应当进行优化 只针对单个流进行停止录制
            if self.args.live and should_stop_record is False and stream.check_record_time(self.args.live_duration):
                should_stop_record = True
                self.logger.debug(
                    f'set should_stop_record flag as {should_stop_record}')
        # 主动停止录制
        if should_stop_record:
            self.stop_record()
        return all_results

    def try_concat(self, stream: Stream):
        if self.args.live is False and self.args.disable_auto_concat is False:
            stream.concat(self.logger, self.args)

    def try_concat_streams(self, streams: List[Stream], selected: List[str]):
        for stream in streams:
            if stream.get_skey() not in selected:
                continue
            if self.args.live is True and self.args.disable_auto_concat is False:
                stream.concat(self.logger, self.args)

    def init_progress(self, stream: Stream, count: int, completed: int):
        if completed > 0:
            if stream.filesize > 0:
                total = stream.filesize
            else:
                total = completed
                stream.filesize = total
        else:
            if stream.filesize > 0:
                total = stream.filesize
            else:
                total = 0
                stream.filesize = total
            completed = 0
        self.xprogress = XProgress(stream.get_name(), len(
            stream.segments), count, total, completed)

    async def do_with_progress(self, loop: AbstractEventLoop, stream: Stream):
        '''
        下载过程输出进度 并合理处理异常
        '''
        results = {}  # type: Dict[bool]
        tasks = set()  # type: Set[Task]

        def _done_callback(_future: Future) -> None:
            nonlocal results
            if _future.exception() is None:
                segment, status, flag = _future.result()
                if flag is None:
                    segment.content = []
                    # self.logger.error('下载过程中出现已知异常 需重新下载\n')
                elif flag is False:
                    segment.content = []
                    # 某几类已知异常 如状态码不对 返回头没有文件大小 视为无法下载 主动退出
                    cancel_all_task()
                    if status in ['STATUS_CODE_ERROR', 'NO_CONTENT_LENGTH']:
                        self.logger.error(
                            f'{status} {t_msg.segment_cannot_download}')
                    elif status == 'EXIT':
                        pass
                    else:
                        self.logger.error(
                            f'{status} {t_msg.segment_cannot_download_unknown_status}')
                results[segment] = flag
            else:
                # 出现未知异常 强制退出全部task
                self.logger.error(
                    f'{t_msg.segment_cannot_download_unknown_exc} => {_future.exception()}\n')
                cancel_all_task()
                results['未知segment'] = False

        def cancel_all_task() -> None:
            for task in tasks:
                task.remove_done_callback(_done_callback)
            for task in filter(lambda task: not task.done(), tasks):
                task.cancel()
        # limit_per_host 根据不同网站和网络状况调整 如果与目标地址连接性较好 那么设置小一点比较好
        count, completed, _left = get_left_segments(stream)
        self.logger.debug(
            f'downloaded count {count}, downloaded size {completed}, left count {len(_left)}')
        if len(_left) == 0:
            return results
        # 没有需要下载的则尝试合并 返回False则说明需要继续下载完整
        self.init_progress(stream, count, completed)
        ts = time.time()
        client = ClientSession(connector=get_connector(
            self.args))  # type: ClientSession
        for segment in _left:
            if segment.max_retry_404 <= 0:
                self.xprogress.decrease_total_count()
                continue
            task = loop.create_task(self.download(client, stream, segment))
            task.add_done_callback(_done_callback)
            tasks.add(task)
        self.logger.info(f'{len(tasks)} tasks start')
        # 阻塞并等待运行完成
        finished, unfinished = await asyncio.wait(tasks)
        # 关闭ClientSession
        await client.close()
        self.xprogress.to_stop()
        self.logger.info(f'tasks end, time used {time.time() - ts:.2f}s')
        return results

    async def download(self, client: ClientSession, stream: Stream, segment: Segment):
        status, flag = 'EXIT', True
        try:
            async with client.get(segment.url + self.args.url_patch, headers=self.args.headers) as resp:
                _flag = True
                self.logger.debug(
                    f'{segment.name} status {resp.status}, {segment.url + self.args.url_patch}')
                if resp.status in [403, 404]:
                    status = 'STATUS_SKIP'
                    flag = False
                    self.xprogress.decrease_total_count()
                    segment.skip_concat = True
                    if resp.status == 404:
                        segment.max_retry_404 -= 1
                if resp.status == 405:
                    status = 'STATUS_CODE_ERROR'
                    flag = False
                if resp.status in self.args.redl_code:
                    status = 'RE-DOWNLOAD'
                    flag = None
                if resp.headers.get('Content-length') is not None:
                    # 对于 filesize 不为 0 后面再另外考虑
                    size = int(resp.headers["Content-length"])
                    stream.filesize += size
                    self.logger.debug(
                        f'{segment.name} response Content-length => {size}')
                    self.xprogress.update_total_size(stream.filesize)
                else:
                    self.logger.debug(
                        f'{segment.name} response header has no Content-length {dict(resp.headers)}')
                    _flag = False
                if flag:
                    while self.terminate is False:
                        data = await resp.content.read(512)
                        if not data:
                            break
                        segment.content.append(data)
                        self.xprogress.add_downloaded_size(len(data))
                        if _flag is False:
                            stream.filesize += len(data)
                            self.logger.debug(
                                f'{segment.name} recv {size} byte data')
                            self.xprogress.update_total_size(stream.filesize)
        except TimeoutError:
            return segment, 'TimeoutError', None
        except client_exceptions.ClientConnectorError:
            return segment, 'ClientConnectorError', None
        except client_exceptions.ClientPayloadError:
            return segment, 'ClientPayloadError', None
        except client_exceptions.ClientOSError:
            return segment, 'ClientOSError', None
        except client_exceptions.ServerDisconnectedError:
            return segment, 'ServerDisconnectedError', None
        except client_exceptions.InvalidURL:
            return segment, 'EXIT', False
        except CancelledError:
            return segment, 'EXIT', False
        except Exception as e:
            self.logger.error(f'! -> {segment.url}', exc_info=e)
            return segment, status, False
        if self.terminate:
            return segment, 'EXIT', False
        if segment.skip_concat:
            return segment, status, True
        if flag is None:
            return segment, status, None
        if flag is False:
            return segment, status, False
        self.xprogress.add_downloaded_count(1)
        self.logger.debug(
            f'{segment.name} download end, size => {sum([len(data) for data in segment.content])}')
        return segment, 'SUCCESS', await self.decrypt(segment, stream)

    async def decrypt(self, segment: Segment, stream: Stream) -> bool:
        '''
        解密部分
        '''
        if self.args.disable_auto_decrypt is True:
            self.logger.debug(f'--disable-auto-decrypt, skip decrypt')
            return segment.dump()
        if segment.is_encrypt() and segment.is_supported_encryption():
            self.logger.debug(
                f'common aes decrypt, key {segment.xkey.key.hex()} iv {segment.xkey.iv}')
            cipher = CommonAES(
                segment.xkey.key, binascii.a2b_hex(segment.xkey.iv))
            return cipher.decrypt(segment)
        else:
            return segment.dump()
