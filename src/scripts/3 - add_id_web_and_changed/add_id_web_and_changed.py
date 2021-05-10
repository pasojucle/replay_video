import sqlite3
from os import path
import shutil
import sys

if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')
    sys.path.append('/home/pi/replay_video/app')

if path.isdir('/home/patrick/python_projects/project_video_raspberry'):
    sys.path.append('/home/patrick/python_projects/project_video_raspberry')
    sys.path.append('/home/patrick/python_projects/project_video_raspberry/app')

import config
from settings import settings
import db
from program import ProgramRepository
from channel import ChannelRepository
from video import VideoRepository
from init_db import init_db
from pprint import pprint


def add_id_web_and_changed():
    database = path.join(config.BASE_DIR, config.DATA_DIR, settings['database'])
    database_sauv = path.join(config.BASE_DIR, config.DATA_DIR, 'v1.7_database_sauv.db')
    if path.isfile(database):
        shutil.copy2(database, database_sauv)

    if path.isfile(database_sauv):
        videos = video_repository.find_all()
        programs = programRepository.find_all()
        channels = channelRepository.find_all()

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