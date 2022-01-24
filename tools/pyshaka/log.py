import logging
import datetime
from pathlib import Path


def setup_logger(name: str, write_to_file: bool = False) -> logging.Logger:
    formatter = logging.Formatter('%(asctime)s %(name)s %(filename)s %(lineno)s : %(levelname)s  %(message)s')
    log_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_folder_path = Path(__name__.split('.')[0], 'logs')
    if log_folder_path.exists() is False:
        log_folder_path.mkdir()

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    lt = logging.getLogger(f'{name}')
    lt.setLevel(logging.DEBUG)
    lt.addHandler(ch)
    if write_to_file:
        log_file_path = log_folder_path / f'{name}-{log_time}.log'
        fh = logging.FileHandler(log_file_path.resolve().as_posix(), encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        lt.addHandler(fh)
        lt.info(f'log file -> {log_file_path}')
    return lt


log = setup_logger('pyshaka')