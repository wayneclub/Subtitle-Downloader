@@ECHO OFF

set/p url="url: "
pip install -r requirement.txt

@REM 下載位置
set output=""
@REM Disney+、HBOGO Asia
set email=""
set password=""
@REM ["en", "zh-Hant", "zh-HK", "zh-Hans", "all"]
set language="zh-Hant"

python subtitle_downloader.py %url% -o %output% -email %email% -password %password% -lang %language%
pause

@@ECHO OFF