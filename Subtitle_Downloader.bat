@@ECHO OFF

set/p url="url: "

@REM Output directory
set output=""
@REM Disney+、HBOGO Asia
set email=""
set password=""
@REM ["en", "zh-Hant", "zh-HK", "zh-Hans", "all"]
set language="zh-Hant"

python subtitle_downloader.py %url% -o %output% -email %email% -password %password% -slang %language%
pause

@@ECHO OFF