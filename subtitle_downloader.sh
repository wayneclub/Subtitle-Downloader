#!/bin/bash

while true; do
    read -p "Url: " url
    python3 subtitle_downloader.py $url
done
