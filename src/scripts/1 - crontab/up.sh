#!/usr/bin/env bash

#cela permet d'ajouter une règle à la liste des règles existantes dans la crontab
#crontab -u pi -l | { cat; echo "*/1 * * * * /usr/bin/python3 /home/pi/replay_video/app/upgrade.py > /dev/null 2>&1"; } | crontab -u pi -
crontab -l | { cat; echo "*/10 * * * * sudo /usr/bin/python3 /home/pi/replay_video/app/upgrade.py > /dev/null 2>&1"; } | crontab -
crontab -l | { cat; echo "*/10 * * * * sudo /usr/bin/python3 /home/pi/replay_video/app/web_service.py > /dev/null 2>&1"; } | crontab -