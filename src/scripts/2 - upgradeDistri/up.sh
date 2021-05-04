#!/usr/bin/env bash

cp ./upgrade_distri.service /etc/systemd/system/upgrade_distri.service

if [ $? -ne 0 ]
then
    exit 1;
fi

systemctl enable upgrade_distri.service
if [ $? -ne 0 ]
then
    exit 2;
fi

systemctl start upgrade_distri.service
if [ $? -ne 0 ]
then
    exit 3;
fi