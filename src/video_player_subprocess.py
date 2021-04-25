import os
import time
from pathlib import Path
import logging
from pprint import pprint
import subprocess
import psutil

from file import File
from video import Video


class VideoPlayer:
    def __init__(self):
        self.omx = None  # ressource du process du player
        self.video_id = None
        self.action = None
        # Masquage de la souris
        subprocess.call("/usr/bin/unclutter -idle 1 -root &", shell=True)

    def pause(self, video):
        if self.is_run(video):
            self.omx.stdin.write(b'p')
            self.omx.stdin.flush()
            self.action = "pause"
            return True

        return False

    def play(self, video):
        self.action = "play"
        if self.is_run(video):
            self.omx.stdin.write(b' ')
            self.omx.stdin.flush()
            return True

        if self.omx:
            self.omx.stdin.write(b'q')
            self.omx.stdin.flush()
            time.sleep(2)

        param = ' -o hdmi'
        video_path = Path(File(video.filename).video)
        pprint(video_path)
        command = f'killall omxplayer;/usr/bin/omxplayer {video_path}'
        try:
            self.omx = subprocess.Popen(f'{command} {param}', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            self.video_id = video.id
            return True
        except BrokenPipeError:
            return False

    def quit(self, video):
        if self.is_run(video):
            self.action = None
            self.omx.stdin.write(b'q')
            self.omx.stdin.flush()
            if self.omx is not None:
                parent_pid = self.omx.pid  # my example
                parent = psutil.Process(parent_pid)

                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        logging.error('--- Try to kill dead process ---')
            self.omx = None
            return True

        return False

    def is_run(self, video):
        if self.omx and self.video_id == video.id:
            return True

        return False

    def get_status(self):
        return {'video_id': self.video_id, 'action': self.action}
