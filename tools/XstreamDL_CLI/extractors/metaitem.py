class MetaItem:
    def generate(self):
        pass

    def to_int(self):
        pass

    def match_duration(self, _duration: str) -> float:
        '''
        test samples
        - PT50M0S
        - PT1H54.600S
        - PT23M59.972S
        - P8DT11H6M41.1367016S
        - P0Y0M0DT0H3M30.000S
        '''
        if isinstance(_duration, str) is False:
            return

        def reset_token():
            nonlocal token_unit, token_time
            token_unit, token_time = '', ''
        offset = 0
        duration = 0.0
        token_unit = ''
        token_time = ''
        t_flag = False
        while offset < len(_duration):
            if _duration[offset].isalpha():
                token_unit += _duration[offset]
            elif _duration[offset].isdigit() or _duration[offset] == '.':
                token_time += _duration[offset]
            else:
                assert False, f'not possible be here _duration => {_duration}'
            offset += 1
            if token_unit == 'P':
                reset_token()
            elif token_unit == 'Y' or (t_flag is False and token_unit == 'M'):
                # 暂时先不计算年和月 有问题再说
                reset_token()
            elif token_unit == 'D':
                duration += 24 * int(token_time) * 60 * 60
                reset_token()
            elif token_unit == 'T':
                t_flag = True
                reset_token()
            elif token_unit == 'H':
                duration += int(token_time) * 60 * 60
                reset_token()
            elif token_unit == 'M':
                duration += int(token_time) * 60
                reset_token()
            elif token_unit == 'S':
                duration += float("0" + token_time)
                reset_token()
        return duration