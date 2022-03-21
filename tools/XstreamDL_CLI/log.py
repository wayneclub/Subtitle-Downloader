import os
import sys
import logging
import datetime
from pathlib import Path


GLOBAL_LOGGERS = {}


def tell_me_path(target_folder_name: str) -> Path:
    '''
    兼容自用脚本版与免安装可执行版本
    :param target_folder_name: 目录文件夹路径
    :returns 返回request_config路径
    '''
    # if getattr(sys, 'frozen', False):
    #     return Path(sys.executable).parent / target_folder_name
    # else:
    #     return Path(__file__).parent.parent / target_folder_name
    return Path(__file__).parent.parent.parent / target_folder_name


class PackagePathFilter(logging.Filter):
    '''
    获取文件相对路径而不只是文件名
    配合行号可以快速定位
    参见 How can I include the relative path to a module in a Python logging statement?
    - https://stackoverflow.com/questions/52582458
    '''

    def filter(self, record):
        record.relativepath = None
        abs_sys_paths = map(os.path.abspath, sys.path)
        for path in sorted(abs_sys_paths, key=len, reverse=True):
            if not path.endswith(os.sep):
                path += os.sep
            if getattr(sys, 'frozen', False):
                record.relativepath = record.pathname
                break
            if record.pathname.startswith(path):
                record.relativepath = os.path.relpath(record.pathname, path)
                break
        return True


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    '''
    - 终端只输出日志等级大于等于level的日志 默认是INFO
    - 全部日志等级的信息都会记录到文件中
    '''
    logger = GLOBAL_LOGGERS.get(name)
    if logger:
        return logger
    # 先把 logger 初始化好
    logger = logging.getLogger(f'{name}')
    GLOBAL_LOGGERS[name] = logger
    # 开始设置
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(relativepath)s:%(lineno)d %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    # formatter = logging.Formatter('%(asctime)s %(process)d %(relativepath)s:%(lineno)d %(levelname)s: %(message)s')
    log_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # 没有打包的时候 __file__ 就是当前文件路径
    # 打包之后通过 sys.executable 获取程序路径
    log_folder_path = tell_me_path('logs')
    if log_folder_path.exists() is False:
        log_folder_path.mkdir()
    ch = logging.StreamHandler()
    ch.addFilter(PackagePathFilter())
    if level.lower() == 'info':
        ch.setLevel(logging.INFO)
    elif level.lower() == 'warning':
        ch.setLevel(logging.WARNING)
    elif level.lower() == 'error':
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    logger.addHandler(ch)
    log_file_path = log_folder_path / f'{name}-{log_time}.log'
    fh = logging.FileHandler(
        log_file_path.resolve().as_posix(), encoding='utf-8', delay=True)
    fh.addFilter(PackagePathFilter())
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def test_log():
    logger = setup_logger("test", level='INFO')
    logger.debug('this is DEBUG level')
    logger.info('this is INFO level')
    logger.warning('this is WARNING level')
    logger.error('this is ERROR level')


# test_log()
