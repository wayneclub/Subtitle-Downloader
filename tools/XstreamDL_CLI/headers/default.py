import sys
import json
from pathlib import Path
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class Headers:
    def __init__(self):
        self.headers = {}

    def get(self, args: CmdArgs) -> dict:
        if getattr(sys, 'frozen', False):
            config_path = Path(sys.executable).parent / args.headers
        else:
            config_path = Path(__file__).parent.parent.parent / args.headers
        if config_path.exists() is False:
            logger.warning(
                f'{config_path.stem} is not exists, put your config file to {config_path.parent.parent.resolve().as_posix()}')
            return
        try:
            self.headers = json.loads(config_path.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(
                f'try to load {config_path.resolve().as_posix()} failed', exc_info=e)
        logger.debug(
            f'use headers:\n{json.dumps(self.headers, ensure_ascii=False, indent=4)}')
        return self.headers
