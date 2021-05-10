from os import path, remove, rename, mkdir, symlink, unlink
import sys


if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')


import logging

import config
from log_gen import LogGen
from web_service import WebService
from video import Video, VideoRepository
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository
from pprint import pprint

web_service = WebService()
logger = LogGen().loggen()
video_repository = VideoRepository()
program_repository = ProgramRepository()
channel_repository = ChannelRepository()
FILE_LOCK = path.join(config.BASE_DIR, config.APP_DIR, "get_video_list.lock")


class DownloadVideoFromWebsite:

    def execute(self):
        logger.info('Téléchargement des vidéos depuis le protail')
        videos = web_service.get_video_list()

        if not self.is_video_list_processing():
            for data in videos.get('videos'):
                f = open(FILE_LOCK, "a")
                f.close()
                if not data.get('program_id'):
                    title = data.get('program')
                    program = ProgramRepository().find_one_by_title(title)
                    if not program:
                        program = Program({'title': data.get('program')}).edit()
                    data['program_id'] = program.id
                    web_service.set_program([program.id, program.title, data.get('program_id_website')])

                if not data.get('channel_id'):
                    channel = ChannelRepository().find_one_by_title(data.get('channel'))
                    if not channel:
                        channel = Channel({'title': data.get('channel')}).edit()
                    data['channel_id'] = channel.id
                    web_service.set_channel([channel.id, channel.title, data.get('channel_id_website')])

                web_service.set_video_status([data.get('id_website'), Video.STATUS_DOWNLOAD_START])
                data['changed'] = 0
                video = Video(data)
                video = video_repository.edit(video)
                video = video.download()
                web_service.set_video(
                    [video.id, video.title, video.broadcast_at, video.program_id, video.channel_id, video.status, data.get('id_website')])
                remove(FILE_LOCK)

    @staticmethod
    def is_video_list_processing():
        return path.isfile(FILE_LOCK)

if __name__ == '__main__':
    DownloadVideoFromWebsite().execute()
