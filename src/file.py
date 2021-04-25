import os
import subprocess
import datetime
import hashlib
from pprint import pprint

from settings import settings

class File:
    def __init__(self, filename):
        self.filename = filename
        self.video = os.path.join(settings['media_dir'], settings['video_dir'], self.filename)
        self.is_file = self.get_is_file()
        self.thumbnail = self.get_thumbnail()
        self.duration = self.get_duration()
        self.md5 = self.getMd5()

    def __str__(self):
        return f"filename: {self.filename}, is_file: {self.is_file}, duration: {self.duration}, md5: {self.md5}"

    def get_is_file(self):
        return os.path.isfile(self.video) and self.video.endswith(('.mp4', 'mkv', 'webm'))

    def get_thumbnail(self):
        if self.is_file:
            title = self.filename.split('.')[:-1][0]
            return os.path.join(settings['media_dir'], settings['thumbnails_dir'], f'{title}.jpg')
        return None

    def get_duration(self):
        if self.is_file:
            bash_command = f'ffmpeg -i {self.video} 2>&1 | grep -o -P "(?<=Duration: ).*?(?=,)"'
            result = subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)

            return datetime.datetime.strptime(result.stdout.strip(), '%H:%M:%S.%f').strftime('%H:%M:%S')

        return None

    def make_thumbnail(self, seconds=9):
        if self.is_file:
            time = str(datetime.timedelta(seconds=seconds))
            bash_command = f'ffmpeg -y -i "{self.video}" -ss {time} -an -s 355x200 -vframes 1 "{self.thumbnail}"'
            subprocess.run(bash_command, shell=True)

    def getMd5(self):
        return hashlib.md5(self.filename.encode('utf-8')).hexdigest()