from pathlib import Path


class CmdArgs:

    def __init__(self):
        self.speed_up = None # type: bool
        self.speed_up_left = None # type: int
        self.live = None # type: bool
        self.compare_with_url = None # type: bool
        self.dont_split_discontinuity = None # type: bool
        self.name_from_url = None # type: bool
        self.live_duration = None # type: float
        self.live_utc_offset = None # type: int
        self.live_refresh_interval = None # type: int
        self.name = None # type: str
        self.base_url = None # type: str
        self.ad_keyword = None # type: str
        self.resolution = None # type: str
        self.best_quality = None # type: bool
        self.video_only = None # type: bool
        self.audio_only = None # type: bool
        self.all_videos = None # type: bool
        self.all_audios = None # type: bool
        self.all_subtitles = None # type: bool
        self.service = None # type: str
        self.save_dir = None # type: Path
        self.ffmpeg = None # type: str
        self.mp4decrypt = None # type: str
        self.mp4box = None # type: str
        self.select = None # type: bool
        self.multi_s = None # type: bool
        self.disable_force_close = None # type: bool
        self.limit_per_host = None # type: int
        self.headers = None # type: str
        self.url_patch = None # type: str
        self.overwrite = None # type: bool
        self.raw_concat = None # type: bool
        self.disable_auto_concat = None # type: bool
        self.enable_auto_delete = None # type: bool
        self.disable_auto_decrypt = None # type: bool
        self.key = None # type: str
        self.b64key = None # type: str
        self.hexiv = None # type: str
        self.proxy = None # type: str
        self.disable_auto_exit = None # type: bool
        self.parse_only = None # type: bool
        self.show_init = None # type: bool
        self.index_to_name = None # type: bool
        self.log_level = None # type: str
        self.redl_code = None # type: list
        self.hide_load_metadata = None # type: bool
        self.no_metadata_file = None # type: bool
        self.gen_init_only = None # type: bool
        self.skip_gen_init = None # type: bool
        self.URI = None # type: list