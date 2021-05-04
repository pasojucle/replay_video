#!/usr/bin/env bash

#on retire la ligne de la crontab
crontab -u pi -l | grep -v "/usr/bin/python3 /home/pi/affidyl/current/parameters.py" | crontab -u pi -
