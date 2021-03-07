import json
import subprocess
from pprint import pprint
import os
import re
import datetime
import unicodedata
import base64

from file import File
from model import ModelRepository
from device import Device

import config

device = Device()

class Video:
    STATUS_DOWNLOAD_NONE = 0
    STATUS_DOWNLOAD_START = 1
    STATUS_DOWNLOAD_SUCCESS = 2
    STATUS_DOWNLOAD_ERROR = 3
    STATUS_FILE_NO_EXIST = 4



    def __init__(self, data):
        self.id = None
        self.title = None
        self.program_id = None
        self.program = None
        self.broadcast_at = None
        self.channel_id = None
        self.channel = None
        self.filename = None
        self.url = None
        self.status = 0
        self.duration = None
        self.parse(data)

    def __str__(self):
        return f"{self.id},{self.title},{self.program_id},{self.program},{self.channel_id},{self.channel},{self.filename},{self.url}, {self.status}"

    def parse(self, data):
        data = dict(data)
        self.id = data.get('id')
        self.title = data.get('title')
        self.program_id = data.get('program_id')
        self.program = data.get('program')
        self.broadcast_at = data.get('broadcast_at')
        self.channel_id = data.get('channel_id')
        self.channel = data.get('channel')
        if data.get('filename') and 'None' != data.get('filename'):
            self.filename = data.get('filename')
        if data.get('duration') and 'None' != data.get('duration'):
            self.duration = data.get('duration')
        if data.get('url') and 'None' != data.get('url'):
            self.url = data.get('url')
        if data.get('status'):
            self.status = data.get('status')

    def make_thumbnail(self, seconds=9):
        File(self.filename).make_thumbnail(seconds)

    def get_thumbnail_encoding(self):
        if self.filename:
            img_filename = os.path.join(config.MEDIA_DIR, config.THUMBNAILS_DIR, self.filename.split(".")[-2] + '.jpg')

            if os.path.isfile(img_filename):
                with open(img_filename, "rb") as image_file:
                    thumbnail_encoding = base64.b64encode(image_file.read()).decode('utf-8')

                return thumbnail_encoding
        return None

    def to_json(self):
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)

    def download(self):
        pprint('download')
        path = os.path.join(config.MEDIA_DIR, config.VIDEOS_DIR)
        full_filename = '_'.join(filter(None,[self.title, self.program, self.channel, self.broadcast_at]))
        regex = re.compile(r"(\s_\s)|([!@#$%^&*()\[\]{};:,/<>?\|\'\"\~\-=+\s•]+)")
        full_filename_no_accents = ''.join((c for c in unicodedata.normalize('NFD', full_filename) if unicodedata.category(c) != 'Mn'))
        full_filename = '_'.join([word for word in full_filename_no_accents.lower().split(' ') if len(word) > 1])
        full_filename = re.sub(regex, '', full_filename)

        download = None
        extensions = None
        extension = None
        try:
            bash_command = "youtube-dl -U"
            pprint(bash_command)
            subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            self.status = self.STATUS_DOWNLOAD_ERROR
        try:
            bash_command = f"youtube-dl -o '{path}/{full_filename}.%(ext)s' {self.url} --restrict-filenames"
            pprint(bash_command)
            # bash_command = ['youtube-dl', '-o', f'{path}/{full_filename}.%(ext)s', self.url, '--restrict-filenames']
            download = subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            pprint(e)
            self.status = self.STATUS_DOWNLOAD_ERROR

        if download:
            extensions = [extension for extension in ['mkv', 'mp4', 'webm']
                          if os.path.isfile(f'{path}/{full_filename}.{extension}')
                          ]

        if extensions:
            extension = extensions[0]

        if extension:
            self.status = self.STATUS_DOWNLOAD_SUCCESS
            self.filename = f'{full_filename}.{extensions[0]}'
            VideoRepository().update_filename(self)
            self.make_thumbnail()
            device.update_video_list()

        VideoRepository().update_status(self)

    def get_duration(self):
        if self.filename and File(self.filename).get_duration():
            pprint(File(self.filename).get_duration())
            return File(self.filename).get_duration()
        return None

    def get_seconds(self):
        if self.duration:
            duration = datetime.datetime.strptime(self.duration, '%H:%M:%S')
            return int((duration - datetime.datetime(1900, 1, 1)).total_seconds())
        return None

    @staticmethod
    def get_status_data():
        return {
            Video.STATUS_DOWNLOAD_NONE: {'text': 'Fichier', 'badge': 'times-circle alert-warning'},
            Video.STATUS_DOWNLOAD_START: {'text': 'Téléchargement en cours...', 'badge': 'loader'},
            Video.STATUS_DOWNLOAD_SUCCESS: {'text': 'Fichier', 'badge': 'check-circle success'},
            Video.STATUS_DOWNLOAD_ERROR: {'text': 'Téléchargement en erreur', 'badge': 'times-circle alert-warning'},
            Video.STATUS_FILE_NO_EXIST: {'text': 'Fichier manquant', 'badge': 'times-circle alert-warning'}
        }


class VideoRepository(ModelRepository):
    @staticmethod
    def get_model():
        return 'Video'

    def find_all(self):
        self.command = '''SELECT v.id, v.title, v.program_id, v.broadcast_at, v.channel_id, v.filename, v.url, v.status, v.duration,
                    p.title AS program, c.title AS channel
                    FROM video AS v
                    INNER JOIN program AS p ON p.id = v.program_id
                    INNER JOIN channel AS c ON c.id = v.channel_id
                    ORDER BY v.broadcast_at DESC
                    ;'''

        return self.getResults()

    def edit(self, video):
        self.param = {
            'title': video.title,
            'program_id': video.program_id,
            'program': video.program,
            'broadcast_at': video.broadcast_at,
            'channel_id': video.channel_id,
            'filename': video.filename,
            'duration': video.duration,
            'status': video.status
        }

        if video.id:
            self.param["id"] = video.id
            self.command = """UPDATE video SET title=:title, program_id=:program_id, broadcast_at=:broadcast_at,
            channel_id=:channel_id, filename=:filename, duration=:duration, status=:status WHERE id=:id"""
            response = self.execute('update')
        else:
            self.param.update({'url': video.url, 'status': video.status})
            self.command = """INSERT INTO video (title, program_id, broadcast_at, channel_id, filename, duration, url, status)
            VALUES (:title, :program_id, :broadcast_at, :channel_id, :filename, :duration, :url, :status)"""
            response = self.execute('insert')


        if not video.id:
            video.id = response

        return video

    def update_filename(self, video):
        self.param = {
            'id': video.id,
            'filename': video.filename,
            'duration': video.get_duration()
        }
        self.command = "UPDATE video SET filename=:filename WHERE id=:id"
        self.execute('update')

    def update_status(self, video):
        self.param = {
            'id': video.id,
            'status': video.status,
        }
        self.command = "UPDATE video SET status=:status WHERE id=:id"
        self.execute('update')

    def find_videos_by_program(self, program_id):
        self.param = {'id': program_id}
        self.command = """SELECT v.id, v.title, v.program_id, v.broadcast_at, v.channel_id, v.filename,
                    p.title AS program
                    FROM video AS v
                    INNER JOIN program AS p ON p.id = v.program_id
                    WHERE p.id=:id ;"""

        return self.getResults()

    def find_by_term(self, term):
        self.param = {'term': f'%{term}%'}
        self.command = "SELECT id, title FROM video WHERE title LIKE :term;"

        return self.getResults()

    def find(self, id):
        self.param = {'id': id}
        self.command = """SELECT v.id, v.title, v.program_id, v.broadcast_at, v.channel_id, v.filename, v.url, v.duration, v.status,
                p.title AS program, c.title AS channel
                FROM video AS v
                INNER JOIN program AS p ON p.id = v.program_id
                INNER JOIN channel AS c ON c.id = v.channel_id
                WHERE v.id=:id"""

        return self.getOneResult()

    def find_all_filenames(self):
        self.command = "SELECT filename FROM video"

        files = self.getResults()

        return [file.filename for file in files]

