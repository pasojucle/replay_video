import os
import subprocess
import re
import unicodedata
from pprint import pprint

import config
from file import File

class Device:
    def __init__(self):
        self.path_videos = os.path.join(config.MEDIA_DIR, config.VIDEOS_DIR)
        self.path_thumbnails = os.path.join(config.MEDIA_DIR, config.THUMBNAILS_DIR)
        self.usb_device = self.mount_usb_device()
        self.file_list = self.get_video_list()

    def get_video_list(self):
        self.file_list = []
        if self.usb_device and os.path.isdir(self.path_videos):
            return {File(filename).md5: File(filename) for filename in os.listdir(self.path_videos) if File(filename).is_file}

    def update_video_list(self):
        self.file_list = self.get_video_list()

    @staticmethod
    def mount_usb_device():
        if not os.listdir(config.MEDIA_DIR):
            try:
                usb_device_is_connected = subprocess.run(f'ls -l /dev/{config.DEVICE}', shell=True, check=True)
            except subprocess.CalledProcessError as e:
                return False

            if usb_device_is_connected:
                try:
                    bash_command = f'mount -t vfat -o utf8 /dev/{config.DEVICE} {config.MEDIA_DIR} -o uid=pi,gid=pi'
                    subprocess.run(['sudo', 'bash', '-c', bash_command])
                except subprocess.CalledProcessError as e:
                    return False

        return True

    @staticmethod
    def unmount_usb_device():
        if os.listdir(config.MEDIA_DIR):
            try:
                bash_command = f'sudo unmount /dev/{config.DEVICE} {config.MEDIA_DIR}'
                subprocess.run(['sudo', 'bash', '-c', bash_command])
            except subprocess.CalledProcessError as e:
                return False

        return True


    def init_videos_dir(self):
        if os.listdir(config.MEDIA_DIR):
            regex = re.compile(r"(\s_\s)|([!@#$%^&*()\[\]{};:,/<>?\|\'\"\~\-=+\s•]+)")

            if not os.path.isdir(self.path_videos):
                os.mkdir(self.path_videos)

            if not os.path.isdir(self.path_thumbnails):
                os.mkdir(self.path_thumbnails)

            for f in os.listdir(config.MEDIA_DIR):
                if os.path.isfile(os.path.join(config.MEDIA_DIR, f)) and f.endswith(('mp4', 'mkv')):
                    source = os.path.join(config.MEDIA_DIR, f)
                    ext = os.path.splitext(f)[1]
                    title = '_'.join([word for word in os.path.splitext(f)[0].lower().split(' ') if len(word) > 1])
                    title_no_accents = ''.join((c for c in unicodedata.normalize('NFD', title) if unicodedata.category(c) != 'Mn'))
                    title = re.sub(regex, '', title_no_accents)
                    video = os.path.join(config.MEDIA_DIR, config.VIDEOS_DIR, f'{title}{ext}')
                    bash_command = f'mv "{source}" "{video}"'
                    subprocess.run(bash_command, shell=True)

        return

    def is_videos_dir_initialized(self):
        return os.path.isdir(self.path_videos) and os.path.isdir(self.path_thumbnails)