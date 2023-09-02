from pathlib import Path
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.models.base import BaseUri
from tools.XstreamDL_CLI.log import setup_logger

logger = setup_logger('XstreamDL', level='INFO')


class BaseParser:
    def __init__(self, args: CmdArgs, uri_type: str):
        self.args = args
        self.uri_type = uri_type
        self.suffix = '.SUFFIX'

    def fix_name(self, name: str):
        '''
        remove illegal char
        '''
        # logger.debug(f'fix name before: {name}')
        exclude_str = ["\\", "/", ":", "：", "*", "?",
                       "\"", "<", ">", "|", "\r", "\n", "\t"]
        for s in exclude_str:
            name = name.replace(s, " ")
        name = "_".join(name.split())
        # logger.debug(f'fix name after: {name}')
        return name

    def dump_content(self, name: str, content: str, suffix: str):
        if self.args.no_metadata_file:
            return
        dump_path = self.args.save_dir / f'{name}{suffix}'
        logger.debug(
            f'save content to {dump_path.resolve().as_posix()}, size {len(content)}')
        dump_path.write_text(content, encoding='utf-8')

    def parse_uri(self, uri: str) -> BaseUri:
        '''
        进入此处的uri不可能是文件夹
        '''
        logger.debug(f'start parse uri for: {uri}')
        rm_manifest = False
        if '.ism' in self.args.base_url and 'manifest' in self.args.base_url:
            rm_manifest = True
        if '.ism' in uri and 'manifest' in uri:
            rm_manifest = True
        name = self.args.name
        if self.uri_type == 'path':
            name = Path(uri).stem
        home_url, base_url = '', ''
        if uri.startswith('http://') or uri.startswith('https://') or uri.startswith('ftp://'):
            uris = uri.split('?', maxsplit=1)
            if name == '':
                name = uris[0][::-1].split('/', maxsplit=1)[0][::-1]
            if name.endswith(self.suffix):
                name = name[:-len(self.suffix)]
            home_url = '/'.join(uris[0].split('/', maxsplit=3)[:-1])
            base_url = uris[0][::-1].split('/', maxsplit=1)[-1][::-1]
        elif Path(uri).exists():
            if name == '':
                name = Path(uri).stem
        if base_url == '' and self.args.base_url != '':
            if rm_manifest and self.args.base_url.rstrip('/').endswith('/manifest'):
                base_url = '/'.join(self.args.base_url.rstrip('/').split('/')
                                    [:-1])
            else:
                base_url = self.args.base_url
            home_url = '/'.join(base_url.split('/', maxsplit=3)[:-1])
        name = self.fix_name(name)
        logger.debug(
            f'parse uri result:\n'
            f'    name {name}\n'
            f'    home_url {home_url}\n'
            f'    base_url {base_url}'
        )
        # return [name, home_url, base_url]
        return BaseUri(name, home_url, base_url)
