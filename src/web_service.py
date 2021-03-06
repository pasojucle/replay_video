import io
import json
import subprocess
import zipfile

from requests.utils import requote_uri

import requests
import logging
from log_gen import LogGen
from pprint import pprint
from os import path, remove, rename, mkdir, symlink, unlink
import re
import urllib

import config
from settings import settings
from video import Video, VideoRepository
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository

VIDEO_LIST_SKELETON = '{0}/ws/videos'
VIDEO_STATUS_SKELETON = '{0}/ws/video/status/{1}/{2}'
VIDEO_SKELETON = '{0}/ws/video/{1}/{2}/{3}/{4}/{5}/{6}/{7}'
PROGRAM_SKELETON = '{0}/ws/program/{1}/{2}/{3}'
CHANNEL_SKELETON = '{0}/ws/channel/{1}/{2}/{3}'
DISTRI_UPDATE_SKELETON = '{0}/ws/update/distri/{1}'
VERSION_LAST_SKELETON = '{0}/ws/version/last'
VERSION_STATUS_SKELETON = '{0}/ws/version/{1}/{2}'

video_repository = VideoRepository()
program_repository = ProgramRepository()
channel_repository = ChannelRepository()
logger = LogGen().loggen()


class WebService:

    def has_video_to_download(self):
        videos = self.__get(VIDEO_LIST_SKELETON.format(settings['ws_uri']))
        if videos:
            return len(videos.get('videos'))

        return 0

    def get_video_list(self):
        logger.debug('Get video list')
        return self.__get(VIDEO_LIST_SKELETON.format(settings['ws_uri']))

    def update_db(self):
        logger.info('update db')
        error = []
        programs = program_repository.find_to_update()
        pprint(programs)
        if programs:
            for program in programs:
                result = self.set_program([program.id, program.title, program.id_web])
                if result:
                    program.id_web = result.get('id_web')
                    program.changed = 0
                    program_repository.edit(program)
                else:
                    error.append(program.title)

        channels = channel_repository.find_to_update()
        if channels:
            for channel in channels:
                result = self.set_channel([channel.id, channel.title, channel.id_web])
                if result:
                    channel.id_web = result.get('id_web')
                    channel.changed = 0
                    program_repository.edit(channel)
                else:
                    error.append(channel.title)
        if not error:
            videos = video_repository.find_to_update()

            if videos:
                for video in videos:
                    data = [video.id, video.title, video.broadcast_at, video.program_id, video.channel_id, video.status, video.id_web]
                    pprint(data)
                    result = self.set_video(data)
                    if result:
                        video.id_web = result.get('id_web')
                        video.changed = 0
                        video_repository.edit(video)

    def set_version_status(self, data):
        self.__get(VERSION_STATUS_SKELETON.format(settings['ws_uri'], *data))

    def set_program(self, data):
        return self.__get(PROGRAM_SKELETON.format(settings['ws_uri'], *data))

    def set_channel(self, data):
        return self.__get(CHANNEL_SKELETON.format(settings['ws_uri'], *data))

    def set_video_status(self, data):
        self.__get(VIDEO_STATUS_SKELETON.format(settings['ws_uri'], *data))

    def set_video(self, data):
        return self.__get(VIDEO_SKELETON.format(settings['ws_uri'], *data))

    def set_distri_upgrade(self, data):
        self.__get(DISTRI_UPDATE_SKELETON.format(settings['ws_uri'], *data))

    def __get(self, url, timeout=30):

        return self.__request(url, 'get', timeout=timeout)

    def __post(self, url, data, timeout=30):
        return self.__request(url, 'post', data=data, timeout=timeout)

    def __request(self, url, method, timeout, data=''):

        try:
            if method == 'get':
                r = requests.get(requote_uri(url), timeout=timeout)
            else:
                r = requests.post(requote_uri(url), timeout=timeout, data=json.dumps(data))

            if r.status_code == 200:
                return r.json()
            else:
                logger.error('Erreur: [%s],  %s inaccessible', r.status_code, url)
                return None

        except requests.Timeout:
            logger.error('Erreur Timeout, %s inaccessible', url)
            return None
        except requests.ConnectionError:
            logger.error('Unable to connect to the portal using %s', url)
            return None
        except ValueError as e:
            logger.error('Trouble with WS values using %s', url)
            logger.error(e)
            return None


if __name__ == '__main__':
    web_service = WebService()
    web_service.get_video_list()

