@@ECHO OFF
:start
cls
set/p url="url: "

set proxy="http://127.0.0.1:7890"

python subtitle_downloader.py %url% -p %proxy%
pause

goto start