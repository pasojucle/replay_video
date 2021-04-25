import json
from requests.utils import requote_uri

import requests
import logging
from pprint import pprint
from os import path, remove

import config
from video import Video, VideoRepository
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository

VIDEO_LIST_SKELETON = '{0}/ws/videos'
VIDEO_STATUS_SKELETON = '{0}/ws/video/status/{1}/{2}'
PROGRAM_SKELETON = '{0}/ws/program/{1}/{2}/{3}'
CHANNEL_SKELETON = '{0}/ws/channel/{1}/{2}/{3}'
RASPBERRY_UPDATE_SKELETON = '{0}/ws/raspberry/update/{1}'

FILE_LOCK = path.join(config.BASE_DIR, config.APP_DIR, "get_video_list.lock")
WS_URI = 'http://replay-video.blng.fr'

video_repository = VideoRepository()

class WebService:
    def has_video_to_download(self):
        videos = self.__get(VIDEO_LIST_SKELETON.format(WS_URI))
        return len(videos.get('videos'))

    @staticmethod
    def is_video_list_processing():
        return path.isfile(FILE_LOCK)

    def get_video_list(self):
        logging.debug('Get video list')
        videos = self.__get(VIDEO_LIST_SKELETON.format(WS_URI))
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
                    self.set_program([program.id, program.title, data.get('program_id_website')])

                if not data.get('channel_id'):
                    channel = ChannelRepository().find_one_by_title(data.get('channel'))
                    if not channel:
                        channel = Channel({'title': data.get('channel')}).edit()
                    data['channel_id'] = channel.id
                    self.set_channel([channel.id, channel.title, data.get('channel_id_website')])

                self.set_video_status([data.get('id_website'), Video.STATUS_DOWNLOAD_START])
                video = Video(data)
                video_repository.edit(video)
                video.download()
                self.set_video_status([data.get('id_website'), video.status])
                remove(FILE_LOCK)

    def set_program(self, data):
        result = self.__get(PROGRAM_SKELETON.format(WS_URI, *data))

    def set_channel(self, data):
        result = self.__get(CHANNEL_SKELETON.format(WS_URI, *data))

    def set_video_status(self, data):
        result = self.__get(VIDEO_STATUS_SKELETON.format(WS_URI, *data))

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
                logging.error('Erreur: [%s],  %s inaccessible', r.status_code, url)
                return None

        except requests.Timeout:
            logging.error('Erreur Timeout, %s inaccessible', url)
            return None
        except requests.ConnectionError:
            logging.error('Unable to connect to the portal using %s', url)
            return None
        except ValueError as e:
            logging.error('Trouble with WS values using %s', url)
            logging.error(e)
            return None

if __name__ == '__main__':
    web_service = WebService()
    web_service.get_video_list()
