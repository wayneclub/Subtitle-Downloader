import os
import platform
from typing import List
from pathlib import Path
from tools.XstreamDL_CLI.cmdargs import CmdArgs
from tools.XstreamDL_CLI.util.texts import t_msg

ONCE_MAX_FILES = 500


class Concat:

    @staticmethod
    def call_mp4decrypt(out_path: Path, args: CmdArgs):
        assert out_path.exists() is True, f'File not exists ! -> {out_path}'
        assert out_path.stat(
        ).st_size > 0, f'File concat failed ! -> {out_path}'
        out = out_path.absolute().as_posix()
        out_decrypted = (
            out_path.parent / f'{out_path.stem}_decrypted{out_path.suffix}').absolute()
        if args.overwrite is False and out_decrypted.exists():
            print(t_msg.decrypted_file_exists_skip)
            return
        if platform.system() == 'Windows':
            _cmd = f'""{args.mp4decrypt}" --show-progress --key {args.key} "{out}" "{out_decrypted.as_posix()}""'
        else:
            _cmd = f'"{args.mp4decrypt}" --show-progress --key {args.key} "{out}" "{out_decrypted.as_posix()}"'
        print(t_msg.start_decrypt)
        os.system(_cmd)
        if args.enable_auto_delete:
            if out_decrypted.exists() and out_decrypted.stat().st_size > 0:
                os.remove(out)

    @staticmethod
    def gen_new_names(names: list, out: str, tmp_suffix: str = '.tmp'):
        work_num = len(names) // ONCE_MAX_FILES + 1
        counts = len(names) // work_num
        new_names = []
        _tmp_outs = []
        for multi_index in range(work_num):
            if multi_index < work_num - 1:
                _names = names[multi_index * counts:(multi_index + 1) * counts]
            else:
                _names = names[multi_index * counts:]
            _tmp_outs.append(f'out{multi_index}{tmp_suffix}')
            new_names.append([_names, f'out{multi_index}{tmp_suffix}'])
        new_names.append([_tmp_outs, out])
        return new_names, _tmp_outs

    @staticmethod
    def gen_cmds_outs(out_path: Path, names: list, args: CmdArgs) -> List[str]:
        out = out_path.absolute().as_posix()
        cmds = []  # type: List[str]
        if args.raw_concat is False:
            if len(names) > ONCE_MAX_FILES:
                new_names, _tmp_outs = Concat.gen_new_names(
                    names, out, tmp_suffix=".ts")
                for _names, _out in new_names:
                    if platform.system() == 'Windows':
                        cmds.append(
                            f'""{args.ffmpeg}" -i concat:"{"|".join(_names)}" -c copy -y "{_out}" > nul"')
                    else:
                        cmds.append(
                            f'"{args.ffmpeg}" -i concat:"{"|".join(_names)}" -c copy -y "{_out}" > nul')
                return cmds, _tmp_outs
            if platform.system() == 'Windows':
                return [f'""{args.ffmpeg}" -i concat:"{"|".join(names)}" -c copy -y "{out}" > nul"'], []
            else:
                return [f'"{args.ffmpeg}" -i concat:"{"|".join(names)}" -c copy -y "{out}" > nul'], []
        if len(names) > ONCE_MAX_FILES:
            new_names, _tmp_outs = Concat.gen_new_names(names, out)
            if platform.system() == 'Windows':
                for _names, _out in new_names:
                    cmds.append(f'copy /b {"+".join(_names)} "{_out}" > nul')
                return cmds, _tmp_outs
            else:
                for _names, _out in new_names:
                    cmds.append(f'cat {" ".join(_names)} > "{_out}"')
                return cmds, _tmp_outs
        if platform.system() == 'Windows':
            return [f'copy /b {"+".join(names)} "{out}"'], []
        else:
            return [f'cat {" ".join(names)} > "{out}"'], []
