import locale


class Texts:
    def __init__(self):
        if locale.getdefaultlocale()[0] == 'zh_CN':
            self.setup_zh_CN()
        else:
            self.setup_en_US()

    def setup_zh_CN(self):
        self.input_stream_number = '请输入要下载流的序号：\n'
        self.select_without_any_stream = '未选择流，退出'
        self.download_start = '下载开始'
        self.segment_cannot_download = '无法下载的m3u8 取消全部下载任务\n'
        self.segment_cannot_download_unknown_status = '出现未知status 取消全部下载任务\n'
        self.segment_cannot_download_unknown_exc = '出现未知异常 强制退出全部task'
        self.cannot_get_stream_metadata = '无法获取视频流信息'
        self.decrypted_file_exists_skip = '解密文件已存在 跳过'
        self.start_decrypt = '开始解密'
        self.total_segments_info_1 = '共计'
        self.total_segments_info_2 = '个分段'
        self.try_to_concat = '尝试合并'
        self.cancel_concat_reason_1 = '但是已经存在合并文件'
        self.cancel_concat_reason_2 = '但是未下载完成'
        self.force_use_raw_concat_for_sample_aes = '发现SAMPLE-AES 将使用二进制合并'

    def setup_en_US(self):
        self.input_stream_number = 'input stream number(s):\n'
        self.select_without_any_stream = 'haven\'t select any stream, exiting'
        self.download_start = 'download start'
        self.segment_cannot_download = 'can not download segment, cancel all downloading task\n'
        self.segment_cannot_download_unknown_status = 'appear unknown status, cancel all downloading task\n'
        self.segment_cannot_download_unknown_exc = 'appear unknown status, force to cancel all downloading task'
        self.cannot_get_stream_metadata = 'cannot get stream metadata'
        self.decrypted_file_exists_skip = 'decrypted file exists, skip it'
        self.start_decrypt = 'start decrypt'
        self.total_segments_info_1 = 'total'
        self.total_segments_info_2 = ' segments'
        self.try_to_concat = 'try to concat'
        self.cancel_concat_reason_1 = 'but file already exists'
        self.cancel_concat_reason_2 = 'buf download not completely'
        self.force_use_raw_concat_for_sample_aes = 'force use --raw-concat for SAMPLE-AES(-CTR)'


t_msg = Texts()


# if __name__ == '__main__':
#     t_msg = Texts()
#     print(t_msg.try_to_concat)