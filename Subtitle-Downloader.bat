@@ECHO OFF
:start
cls
set/p url="url: "

python subtitle_downloader.py %url%
pause

goto start