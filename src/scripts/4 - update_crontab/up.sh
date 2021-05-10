#!/usr/bin/env bash

#cela permet d'ajouter une règle à la liste des règles existantes dans la crontab
crontab -l | grep -v "sudo /usr/bin/python3 /home/pi/replay_video/app/web_service.py" | crontab -
crontab -l | { cat; echo "*/10 * * * * sudo /usr/bin/python3 /home/pi/replay_video/app/download_video_from_website.py > /dev/null 2>&1"; } | crontab -