from pprint import pprint
import subprocess

import config
from device import Device

from video import Video, VideoRepository
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository

def poweroff():
    bash_command = f'umount {config.VIDEOS_DIR}'
    subprocess.run(['sudo', 'bash', '-c', bash_command])
    subprocess.run(['sudo', 'bash', '-c', 'poweroff'])
    return


if __name__ == '__main__':
    device = Device()



