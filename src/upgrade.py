import io
import logging
import zipfile
import requests
import subprocess

from os import path, rename, mkdir, symlink, unlink, scandir, walk, chdir, chmod, stat as ostat, getcwd
import stat
from shutil import copytree
import sys

if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')
from log_gen import LogGen
import config
from web_service import WebService
from settings import settings
from pprint import pprint

web_service = WebService()
logger = LogGen().loggen()


class Upgrade:
    tmp_dir = '/home/patrick/Téléchargements'

    def __init__(self):
        self.tag = None
        self.dst = None
        self.link = path.join(config.BASE_DIR, 'app')

    def __str__(self):
        return f"tag : {self.tag}"

    def execute(self):
        self.get_new_version()
        if self.tag:
            self.download_new_version()
            if settings['env'] == 'prod':
                self.execute_scripts()
                self.change_version()
                self.reboot()

    def get_new_version(self):
        logger.info('Get version')
        bash_command = "git fetch && git tag"
        try:
            result = subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)
            versions = result.stdout.splitlines()
            versions.sort(reverse=True)
        except subprocess.CalledProcessError as e:
            logger.error(e)
            return None

        tag = versions[0] if versions else None

        if tag and tag[1:] > settings['version'][1:]:
            self.tag = tag
            self.dst = path.join(config.BASE_DIR, config.VERSION_DIR, self.tag)
            return self.tag

        return None

    def download_new_version(self):
        url = f"{settings['update_uri']}{self.tag}.zip"
        logger.info('Start downloading ( %s )', url)
        web_service.set_version_status([self.tag, 1])
        r = requests.get(url, allow_redirects=True)

        if r.status_code != 200:
            logger.error(f"[{r.status_code}] Error while downloading: unable to communicate with server at {url}")
            return None

        z = zipfile.ZipFile(io.BytesIO(r.content))
        filename = z.namelist()[0]
        z.extractall(self.tmp_dir)
        src = path.join(self.tmp_dir, filename, 'src')

        status = 2
        if not path.isdir(path.join(self.tmp_dir, filename)):
            status = 3
            web_service.set_version_status([self.tag, status])
            return status

        if not path.isdir(path.join(config.BASE_DIR, config.VERSION_DIR)):
            mkdir(path.join(config.BASE_DIR, config.VERSION_DIR))

        rename(src, self.dst)

        if not path.isdir(self.dst):
            status = 3
            web_service.set_version_status([self.tag, status])

        return status

    def change_version(self):
        status = 2

        if path.islink(self.link):
            unlink(self.link)

        symlink(self.dst, self.link)

        settings['version'] = self.tag
        settings.save()

        web_service.set_version_status([self.tag, status])
        return status

    def execute_scripts(self):
        logger.info('Start task execute_script')

        script_path = path.join(config.BASE_DIR, config.VERSION_DIR, self.tag, 'scripts')
        control_path = path.join(config.BASE_DIR, config.DATA_DIR, 'scripts')
        current_path = getcwd()

        if not path.isdir(control_path):
            mkdir(control_path)

        logger.info(script_path)

        if not path.isdir(script_path):
            logger.error('%s did not exist', script_path)
            return None

        installed = []
        for script in scandir(control_path):
            if script.is_dir():
                installed.append(script.name)

        for roots, dir, files in walk(control_path):
            installed.extend(dir)

        script_list = []
        for script in scandir(script_path):
            if script.is_dir():
                script_list.append(script.name)

        to_install = set(script_list) - set(installed)
        logger.info(to_install)

        status = 2
        for script_name in to_install:
            script_dir = path.join(script_path, script_name)
            logger.info(script_dir)
            script_link = './up.sh'

            chdir(script_dir)
            st = ostat(script_link)

            chmod(script_link, st.st_mode | stat.S_IEXEC)

            try:
                result = subprocess.run(['bash', '-c', script_link], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f'Erreur lors de l\'exéctution du script {script_link}')
                status = 3
            #
            # if result.returncode != 0:
            #     logger.error(f'Erreur lors de l\'exéctution du script {script_link}')
            #     status = 3

            copytree(script_dir, path.join(control_path, script_name))

        chdir(current_path)

        web_service.set_version_status([self.tag, status])

        return status

    @staticmethod
    def reboot():
        if settings['env'] == 'prod':
            subprocess.call(['reboot'])

if __name__ == '__main__':
    upgrade = Upgrade()
    upgrade.execute()
    # pprint(upgrade.get_new_version())
    # upgrade.execute_scripts('v1.2')
