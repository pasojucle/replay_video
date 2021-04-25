#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path, getenv, stat, remove, listdir
from pathlib import Path
from sys import exit
from configparser import ConfigParser, Error, ParsingError
import shutil
import logging
import sys
from collections import UserDict
from pprint import pprint

import config
CONFIG_DIR = path.join(config.BASE_DIR, config.DATA_DIR)
CONFIG_FILE = 'replay_video.conf'
CONFIG_LOCK = 'replay_video.lock'

DEFAULTS = {
    'main': {
        'database': 'database.db',
        'ws_uri': 'http://replay-video.blng.fr',
        'port_usb': 'sda1',
        'media_dir': '/media/usb',
        'video_dir': 'videos',
        'thumbnails_dir': 'thumbnails',
        'update_uri': 'https://github.com/pasojucle/replay_video/archive/refs/tags/',
        'version': 'v0.0',
        'env': 'prod',
    },
}

class Settings(UserDict):

    def __init__(self, *args, **kwargs):
        UserDict.__init__(self, *args, **kwargs)
        self.home = config.DATA_DIR
        self.conf_file = self.get_configfile()
        self.conf_lock = self.get_configlock()

        if not path.isfile(self.conf_file):
            logging.error('Config-file %s missing', self.conf_file)
            logging.error('Create default file')
            self.save()
        else:
            self.load()

    def _get(self, config, section, field, default):
        try:
            if isinstance(default, bool):
                self[field] = config.getboolean(section, field)
            elif isinstance(default, int):
                self[field] = config.getint(section, field)
            else:
                self[field] = config.get(section, field)
        except Error as e:
            logging.info("Could not parse setting '%s.%s': %s. Using default value: '%s'." % (section, field, e, default))
            self[field] = default


    def _set(self, config, section, field, default):

        if isinstance(default, bool):
            config.set(section, field, self.get(field, default) and 'on' or 'off')
        else:
            config.set(section, str(field), str(self.get(field, default)))

    def load(self):
        """Loads the latest settings from replay_video.conf into memory."""
        logging.debug('Reading config-file...')
        config = ConfigParser()

        if not path.isfile(self.conf_file):
            logging.error('Config-file %s missing', self.conf_file)
            if path.isfile(self.conf_file + ".bak"):
                logging.info('Restore backup')
                shutil.copy2(self.conf_file + ".bak", self.conf_file)

        file_size = stat(self.conf_file).st_size
        if file_size == 0 and not path.exists(self.conf_lock):
            shutil.copy2(self.conf_file + ".bak", self.conf_file)
            logging.info('Backup installed')
        try:
            config.read(self.conf_file)
        except ParsingError:
            with open(self.conf_file, "w") as f:
                content = f.read()
                content.rstrip('\x00')
                f.write(content)

        for section, defaults in DEFAULTS.items():
            for field, default in defaults.items():
                self._get(config, section, field, default)

    def save(self):
        # Write new settings to disk.
        config = ConfigParser()
        for section, defaults in DEFAULTS.items():
            config.add_section(section)
            for field, default in defaults.items():
                self._set(config, section, field, default)
        Path(self.conf_lock).touch()
        with open(self.conf_file, "w") as f:
            config.write(f)

        remove(self.conf_lock)

        self.load()

    def get_configdir(self):
        return path.join(self.home, CONFIG_DIR)

    def get_configfile(self):
        return path.join(CONFIG_DIR, CONFIG_FILE)

    def get_configlock(self):
        return path.join(CONFIG_DIR, CONFIG_LOCK)

    def check_user(self, user, password):
        if not self['user'] or not self['password']:
            logging.debug('Username or password not configured: skip authentication')
            return True

        return self['user'] == user and self['password'] == password


settings = Settings()
old_settings = Settings()
