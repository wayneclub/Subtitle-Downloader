@@ECHO OFF

set/p URL="下載網址："
pip install -r requirement.txt
python subtitle_downloader.py %URL%
pause

@@ECHO OFF