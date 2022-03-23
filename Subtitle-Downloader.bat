@@ECHO OFF
:start
cls
set/p url="url: "

@REM Output directory
set output=""
@REM Disney+、HBOGO Asia
set email=""
set password=""
@REM ["en", "zh-Hant", "zh-HK", "zh-Hans", "all"]
set slang="zh-Hant"

set proxy=""

python subtitle_downloader.py %url% -o %output% -email %email% -password %password% -slang %slang% -p %proxy%
pause

goto start