import io
import logging
import zipfile
import requests
import subprocess

from os import path, rename, mkdir, symlink, unlink

import config
from web_service import WebService
from settings import settings
from pprint import pprint

web_service = WebService()


class Upgrade:
    tmp_dir = '/home/patrick/Téléchargements'

    def upgrade(self):
        tag = web_service.get_new_version()

        if tag:
            self.change_version(tag)
            self.restart_services()

    def change_version(self, tag):
        url = f"{settings['update_uri']}{tag}.zip"
        logging.info('Start downloading ( %s )', url)
        web_service.set_version_status([tag, 1])
        r = requests.get(url, allow_redirects=True)
        pprint(r.status_code)
        if r.status_code != 200:
            logging.error(f"[{r.status_code}] Error while downloading: unable to communicate with server at {url}")
            return None

        z = zipfile.ZipFile(io.BytesIO(r.content))
        filename = z.namelist()[0]
        z.extractall(self.tmp_dir)
        src = path.join(self.tmp_dir, filename, 'app')
        dst = path.join(config.BASE_DIR, config.VERSION_DIR, tag)
        link = path.join(config.BASE_DIR, 'app')

        status = 2
        if not path.isdir(path.join(self.tmp_dir, filename)):
            status = 3
            web_service.set_version_status([tag, status])
            return status

        if not path.isdir(path.join(config.BASE_DIR, config.VERSION_DIR)):
            mkdir(path.join(config.BASE_DIR, config.VERSION_DIR))
        rename(src, dst)

        if not path.isdir(dst):
            status = 3
            web_service.set_version_status([tag, status])
            return status

        if path.islink(link):
            unlink(link)
        symlink(dst, link)

        settings['version'] = tag
        settings.save()

        web_service.set_version_status([tag, status])
        return status

    @staticmethod
    def restart_services():
        if settings['env'] == 'prod':
            subprocess.call(['service', 'nginx', 'restart'])
            subprocess.call(['systemctl', 'replay_video.service', 'restart'])

if __name__ == '__main__':
    upgrade = Upgrade()
    upgrade.upgrade()
