import sqlite3
from os import path
import shutil
import sys

if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')
    sys.path.append('/home/pi/replay_video/version/v1.7')

if path.isdir('/home/patrick/python_projects/project_video_raspberry'):
    sys.path.append('/home/patrick/python_projects/project_video_raspberry')
    sys.path.append('/home/patrick/python_projects/project_video_raspberry/app')

import config
from settings import settings
import db
from program import Program
from channel import Channel
from video import Video
from init_db import init_db
from pprint import pprint


def add_id_web_and_changed():
    database = path.join(config.BASE_DIR, config.DATA_DIR, settings['database'])
    database_sauv = path.join(config.BASE_DIR, config.DATA_DIR, 'v1.7_database_sauv.db')
    if path.isfile(database):
        shutil.copy2(database, database_sauv)

    if path.isfile(database_sauv):
        command = '''SELECT v.id, v.title, v.program_id, v.broadcast_at, v.channel_id, v.filename, v.url, v.status, v.duration,
                    p.title AS program, c.title AS channel
                    FROM video AS v
                    INNER JOIN program AS p ON p.id = v.program_id
                    INNER JOIN channel AS c ON c.id = v.channel_id
                    ORDER BY v.broadcast_at DESC
                    ;'''

        results = db.execute_queries([db.Query(command)])
        videos = [Video(data) for data in results]

        command = 'SELECT * FROM program ORDER BY title ASC;'
        results = db.execute_queries([db.Query(command)])
        programs = [Program(data) for data in results]

        command = 'SELECT * FROM channel ORDER BY title ASC;'
        results = db.execute_queries([db.Query(command)])
        channels = [Channel(data) for data in results]

        init_db()
        programs_str = ", ".join([f"({program.id},\"{program.title}\")" for program in programs])
        channels_str = ", ".join([f"({channel.id},\"{channel.title}\")" for channel in channels])
        videos_str = ", ".join([f"({video.id},\"{video.title}\",{video.program_id},\"{video.broadcast_at}\",{video.channel_id},\"{video.filename}\",\"{video.duration}\",\"{video.url}\",{video.status})" for video in videos])

        commands = [
            f'INSERT INTO program (id, title) VALUES {programs_str};',
            f'INSERT INTO channel (id, title) VALUES {channels_str};',
            f'INSERT INTO video (id, title, program_id, broadcast_at, channel_id, filename, duration, url, status) VALUES {videos_str};'
        ]
        queries = [db.Query(command) for command in commands]

        db.execute_queries(queries)


if __name__ == "__main__":
    video_repository = VideoRepository()
    programRepository = ProgramRepository()
    channelRepository = ChannelRepository()
    add_id_web_and_changed()