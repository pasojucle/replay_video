from pprint import pprint
import subprocess

import config
import settings
from device import Device

from video import Video, VideoRepository
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository

def poweroff():
    bash_command = f"umount {settings['video_dir']}"
    subprocess.run(['sudo', 'bash', '-c', bash_command])
    subprocess.run(['sudo', 'bash', '-c', 'poweroff'])
    return


if __name__ == '__main__':
    device = Device()


