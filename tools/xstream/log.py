import sys
import logging
import datetime
from pathlib import Path


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    '''
    - 终端只输出日志等级大于等于level的日志 默认是INFO
    - 全部日志等级的信息都会记录到文件中
    '''
    formatter = logging.Formatter('%(asctime)s %(name)s %(filename)s %(lineno)s : %(levelname)s  %(message)s')
    log_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # 没有打包的时候 __file__ 就是当前文件路径
    # 打包之后通过 sys.executable 获取程序路径
    if getattr(sys, 'frozen', False):
        app_path = Path(sys.executable).parent
    else:
        app_path = Path(__file__).parent.parent
    log_folder_path = app_path / 'logs'
    if log_folder_path.exists() is False:
        log_folder_path.mkdir()
    ch = logging.StreamHandler()
    if level.lower() == 'info':
        ch.setLevel(logging.INFO)
    elif level.lower() == 'warning':
        ch.setLevel(logging.WARNING)
    elif level.lower() == 'error':
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger = logging.getLogger(f'{name}')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    log_file_path = log_folder_path / f'{name}-{log_time}.log'
    fh = logging.FileHandler(log_file_path.resolve().as_posix(), encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info(f'log file -> {log_file_path.resolve().as_posix()}')
    return logger


def test_log():
    logger = setup_logger("test", level='INFO')
    logger.debug('this is DEBUG level')
    logger.info('this is INFO level')
    logger.warning('this is WARNING level')
    logger.error('this is ERROR level')


# test_log()