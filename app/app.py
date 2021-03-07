from pprint import pprint
import subprocess

import config
from device import Device
from model import Model, ModelRepository

from video import Video


class Program(Model):
    @staticmethod
    def get_table():
        return 'program'


class Channel(Model):
    @staticmethod
    def get_table():
        return 'channel'


class ProgramRepository(ModelRepository):
    @staticmethod
    def get_model():
        return 'Program'


class ChannelRepository(ModelRepository):
    @staticmethod
    def get_model():
        return 'Channel'


def poweroff():
    bash_command = f'umount {config.VIDEOS_DIR}'
    subprocess.run(['sudo', 'bash', '-c', bash_command])
    subprocess.run(['sudo', 'bash', '-c', 'poweroff'])
    return

def get_globals():
    return globals()

if __name__ == '__main__':
    device = Device()
    modelA = Model()
    model_repository = ModelRepository()
    # pprint(device.file_list)
    # pprint(video_list())


