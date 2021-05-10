#!/usr/bin/env bash

/usr/bin/python3 ./add_id_web_and_changed.py
if [ $? -ne 0 ]
then
    exit 1;
fi
