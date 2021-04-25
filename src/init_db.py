import sqlite3
import config
import os
import db
import re

from app import ProgramRepository, ChannelRepository
from video import VideoRepository
from pprint import pprint



def init_db():
    with open (os.path.join(config.CWD, 'schema.sql')) as f:
        # db.execute_queries(f.read().decode('utf8'))
        queries = [db.Query(re.sub(r"[\n\t\s]+", " ", command)) for command in f.read().split(';') if command]
        db.execute_queries(queries)


def convert_db():
    command = "SELECT title, program, broadcast_at, channel, filename, duration FROM video"
    response = db.execute_queries([db.Query(command)])

    program_list = list(set([dict(data).get('program') for data in response if dict(data).get('program')]))
    programs = {}
    [programs.update({program: i+1}) for i, program in enumerate(program_list)]
    channel_list = list(set([dict(data).get('channel') for data in response if dict(data).get('channel')]))
    channels = {}
    [channels.update({channel: i+1}) for i, channel in enumerate(channel_list)]
    init_db()

    programs_str = ", ".join([f"({index},\"{title}\")" for title, index in programs.items()])
    pprint(programs_str)
    channels_str = ", ".join([f"({index},\"{title}\")" for title, index in channels.items()])
    commands = [
        f'INSERT INTO program (id, title) VALUES {programs_str};',
        f'INSERT INTO channel (id, title) VALUES {channels_str};'
    ]
    queries = [db.Query(command) for command in commands]
    db.execute_queries(queries)

    for data in response:
        data = dict(data)
        video_data = {
            'title': data.get('title'),
            'program_id': programs[data.get('program')] if data.get('program') else None,
            'broadcast_at': data.get('broadcast_at'),
            'channel_id': channels[data.get('channel')] if data.get('channel') else None,
            'filename': data.get('filename')
        }
        video_repository.edit(video_data)

    command = '''SELECT v.id, v.title, v.program_id, v.broadcast_at, v.channel_id, v.filename,
                p.title AS program, c.title AS channel
                FROM video AS v
                INNER JOIN program AS p ON p.id = v.program_id INNER JOIN channel AS c ON c.id = v.channel_id;'''
    videos = db.execute_queries([db.Query(command)])

    [pprint(Video(video).__str__()) for video in videos]
    [pprint(f"{video.title},{video.program},{video.channel},{video.filename}") for video in video_repository.find_all()]


def change_filename_nullable():
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
    # init_db()
    # convert_db()
    change_filename_nullable()