#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
import sys
from os import path
import inspect
import base64
import json
import re
from pprint import pprint
if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')

import config
from pathlib import Path

sys.path.append(path.join(config.BASE_DIR, config.APP_DIR))
from app import poweroff
from program import Program, ProgramRepository
from channel import Channel, ChannelRepository
from video import Video, VideoRepository
from device import Device
from file import File
from network import Network
from web_service import WebService
from upgrade import Upgrade

from settings import settings

app = Flask(__name__)
device = Device()
video_repository = VideoRepository()
program_repository = ProgramRepository()
channel_repository = ChannelRepository()
network = Network()
web_service = WebService()
upgrade = Upgrade()

if settings['env'] == 'prod':
    from video_player_subprocess import VideoPlayer
    video_player = VideoPlayer()

@app.route("/", methods=['GET', 'POST'])
def home():
    videos = video_repository.find_all()
    device.init_videos_dir()
    device.mount_usb_device()
    tag = upgrade.get_new_version()

    if request.method == 'POST':
        data = dict(request.form)
        search = data.get('search')
        if search:
            if search.startswith('v-', 0, 2):
                id = search[2:]
                return redirect(url_for('video_show', video_id=id))

            if search.startswith('p-', 0, 2):
                id = search[2:]
                videos = video_repository.find_videos_by_program(id)

    return render_template("home.html", video_list=videos, file_list=device.file_list,
                           program_list=program_repository.find_all(), tag=tag)


@app.route("/video/show/<video_id>", methods=['GET', 'POST'])
def video_show(video_id):
    video = video_repository.find(video_id)
    context = {
        'fromisoformat': date.fromisoformat,
        'strftime': date.strftime}
    encoded_thumbnail = None

    if video.filename:
        if not File(video.filename).is_file:
            video.status = Video.STATUS_FILE_NO_EXIST
            video_repository.update_status(video)

        encoded_thumbnail = video.get_thumbnail_encoding()

    action = None
    if video_player.get_status().get('video_id') == video.id:
        action = video_player.get_status().get('action')

    render = render_template("video_show.html", video=video, image=encoded_thumbnail,
                             status_data=video.get_status_data(), action=action,
                             **context)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'render': render, 'status': video.status})

    return render


@app.route("/video/download/ajax", methods=['POST'])
def video_download():
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = dict(request.form)
        video_id = data.get('video_id')

    video = video_repository.find(video_id)

    if video.url is not None and video.status < 2:
        if video.status == Video.STATUS_DOWNLOAD_NONE:
            video.download()

    return jsonify(response=1)


@app.route("/ws/video/list/ajax", methods=['GET'])
def ws_video_list():
    web_service.get_video_list()

    return jsonify(response=1)


@app.route("/video/add/<filename>", defaults={"video_id": None}, methods=['GET', 'POST'])
@app.route("/video/edit/<video_id>", defaults={"filename": None}, methods=['GET', 'POST'])
def video_edit(video_id, filename):
    video = None
    if video_id:
        video = video_repository.find(video_id)
        file = None
        if video.filename:
            filename = video.filename

    if filename:
        file = File(filename)

    if request.method == 'POST':
        data = dict(request.form)
        md5 = data.get('file')
        program_data = data.get('program_id')
        channel_data = data.get('channel_id')

        if program_data.startswith('#', 0, 1):
            program = Program({'title': program_data[1:]}).edit()
            data['program_id'] = program.id

        if channel_data.startswith('#', 0, 1):
            channel = Channel({'title': channel_data[1:]}).edit()
            data['channel_id'] = channel.id

        if md5:
            file = device.file_list.get(md5)
            data['filename'] = file.filename
            data['duration'] = file.duration
            data['status'] = Video.STATUS_DOWNLOAD_SUCCESS

            video = video_repository.edit(Video(data))

            return redirect(url_for('video_show', video_id=video.id))

    return render_template("video_edit.html", video=video, file_list=device.file_list,
                           program_list=program_repository.find_all(), channel_list=channel_repository.find_all(),
                           current_file=file)


@app.route("/shutdown", methods=['POST'])
def shutdown():
    poweroff()
    return jsonify({'result': 1})


@app.route("/mount/usb/device")
def mount_usb_device():
    device.mount_usb_device()
    return redirect(url_for('tools'))


@app.route("/unmount/usb/device")
def unmount_usb_device():
    device.unmount_usb_device()
    return redirect(url_for('tools'))


@app.route("/init/videos/dir")
def init_videos_dir():
    device.init_videos_dir()
    return redirect(url_for('tools'))


@app.route("/download/add", defaults={"video_id": None}, methods=['GET', 'POST'])
@app.route("/download/edit/<video_id>", methods=['GET', 'POST'])
def download_add(video_id):
    video = None
    if video_id:
        video = video_repository.find(video_id)

    if request.method == 'POST':
        data = dict(request.form)
        if data.get('program_id'):
            program = Program({'id': data['program_id']}).add_if_not_exist()
            data.update({'program_id': program.id, 'program': program.title})
        channel = Channel({'id': data['channel_id']}).add_if_not_exist()
        data.update({'channel_id': channel.id, 'channel': channel.title})
        video = video_repository.edit(Video(data))

        return redirect(url_for('video_show', video_id=video.id))

    return render_template("download_add.html", program_list=program_repository.find_all(),
                           channel_list=channel_repository.find_all(), today=date.today().strftime("%Y-%m-%d"),
                           video=video)


@app.route("/video/reload/<video_id>", methods=['POST'])
def video_reload(video_id):
    if video_id:
        video_repository.update_status(Video({'id': video_id, 'status': Video.STATUS_DOWNLOAD_NONE}))

        # return jsonify({'result': 1})
        return redirect(url_for('video_show', video_id=video_id))


@app.route("/video/play/<video_id>", methods=['POST'])
def video_play(video_id):
    result = 0
    target = '#play'
    if video_id:
        video = video_repository.find(video_id)
        result = video_player.play(video)

    return jsonify({'result': result, 'target': target})


@app.route("/video/pause/<video_id>", methods=['POST'])
def video_pause(video_id):
    result = 0
    target = '#pause'
    if video_id:
        video = video_repository.find(video_id)
        result = video_player.pause(video)

    return jsonify({'result': result, 'target': target})


@app.route("/video/quit/<video_id>", methods=['POST'])
def video_quit(video_id):
    result = 0
    target = None
    if video_id:
        video = video_repository.find(video_id)
        result = video_player.quit(video)

    return jsonify({'result': result, 'target': target})


@app.route("/tools")
def tools():
    network_addresses = network.get_ip_config()

    services = [
        {'label': 'Disques', 'value': device.usb_device},
        {'label': 'Réseau éthernet', 'value': network_addresses.get('eth0')},
        {'label': 'Réseau wifi', 'value': network_addresses.get('wlan0')},
    ]

    return render_template("tools.html", services=services, device=device)


@app.route("/database/list")
def database_list():
    database_list = [
        {
            'title': 'Emissions',
            'id': 'program_id',
            'all_items': program_repository.find_all()
        },
        {
            'title': 'Chaînes',
            'id': 'channel_id',
            'all_items': channel_repository.find_all()
        }
    ]

    return render_template("database_list.html", database_list=database_list)


@app.route("/program/edit/<program_id>", defaults={"channel_id": None}, methods=['GET', 'POST'])
@app.route("/channel/edit/<channel_id>", defaults={"program_id": None}, methods=['GET', 'POST'])
def database_edit(program_id, channel_id):
    if program_id:
        repository = program_repository
        item = repository.find(program_id)

    if channel_id:
        repository = channel_repository
        item = repository.find(channel_id)

    if request.method == 'POST':
        data = dict(request.form)
        title = data.get('title')
        if title:
            item.title = title
            repository.update_title(item)
            return redirect(url_for("database_list"))

    return render_template("database_edit.html", item=item)


@app.route("/program/delete/<program_id>", defaults={"channel_id": None}, methods=['GET', 'POST'])
@app.route("/channel/delete/<channel_id>", defaults={"program_id": None}, methods=['GET', 'POST'])
def database_delete(program_id, channel_id):
    if program_id:
        repository = program_repository
        item = repository.find(program_id)
        modal_title = "Supprimer une émission"
        modal_message = f"Confirmez-vous la suppression de l'émission {item.title}"

    if channel_id:
        repository = channel_repository
        item = repository.find(channel_id)
        modal_title = "Supprimer une chaîne"
        modal_message = f"Confirmez-vous la suppression de la chaîne {item.title}"

    if request.method == 'POST':
        repository.delete(item)
        return redirect(url_for("database_list"))

    return render_template("database_delete.html", program_id=program_id, channel_id=channel_id,
                           modal_title=modal_title, modal_message=modal_message)


@app.route("/video/new")
def video_new():
    unassigned_files = [file for i, (cle, file) in enumerate(device.file_list.items())
                        if file.filename not in video_repository.find_all_filenames()]

    return render_template("video_new.html", unassigned_files=unassigned_files)


@app.route("/video/thumbnail/<video_id>", methods=['get', 'post'])
def video_thumbnail(video_id):
    if video_id:
        video = video_repository.find(video_id)

    if request.method == 'POST':
        data = dict(request.form)
        id = data.get('videoId')
        seconds = data.get('seconds')
        video = video_repository.find(id)
        video.make_thumbnail(int(seconds))
        return redirect(url_for('video_show', video_id=id))

    return render_template("video_thumbnail.html", video=video)


@app.route("/network/edit", methods=['get', 'post'])
def network_edit():
    network_data = network.get_wifi()

    if request.method == 'POST':
        network_data = dict(request.form)
        if network_data.get('dhcp'):
            network_data['dhcp'] = filter_var(network_data.get('dhcp'), 'bool')
        if network_data.get('dns'):
            network_data['dns'] = filter_var(network_data.get('dns'), 'bool')

        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            if network.set_wifi(network_data):
                network.reload_network_interface

            return redirect(url_for('tools'))

    render = render_template("network_edit.html", network=network_data)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'render': render})

    return render

@app.route("/settings/edit", methods=['GET', 'POST'])
def settings_edit():

    if request.method == 'POST':
        new_settings = dict(request.form)
        if str(settings) != str(new_settings):
            for key, value in settings.items():
                settings[key] = new_settings[key]
                settings.save()
        return redirect(url_for('tools'))

    return render_template("settings_edit.html", settings=settings)


@app.route("/version/upgrade/", methods=['POST', 'GET'])
def version_upgrade():
    if request.method == 'GET':
        # tag = web_service.get_new_version()
        tag = upgrade.get_new_version()
        status = 0
    else:
        data = dict(request.form)
        tag = data.get('tag')
        status = upgrade.change_version(tag)

    return render_template("version_upgrade.html", tag=tag, status=status)


@app.route("/video/list/", methods=['POST'])
def video_list_ajax():
    data = dict(request.form)
    term = data.get('term')
    if term:
        videos = video_repository.find_by_term(term)
        programs = program_repository.find_by_term(term)
    else:
        videos = video_repository.find_all()
        programs = program_repository.find_all()

    result = [{'id': f"v-{video.id}", 'text': video.title} for video in videos]
    result.extend([{'id': f"p-{program.id}", 'text': program.title} for program in programs])
    return json.dumps({'results': result})


@app.route("/videos/status/", methods=['GET'])
def videos_status_ajax():
    videos_status = [
        {'label': 'À télécharger', 'value': web_service.has_video_to_download()},
        {'label': 'En chargement', 'value': len(video_repository.find_videos_by_status(Video.STATUS_DOWNLOAD_START))},
        {'label': 'En erreur', 'value': len(video_repository.find_videos_by_status(Video.STATUS_DOWNLOAD_ERROR))},
    ]

    is_video_list_processing=web_service.is_video_list_processing()
    render = render_template("videos_status.html", videos_status=videos_status,
                             is_video_list_processing=is_video_list_processing)

    return jsonify({'render': render, 'is_video_list_processing': is_video_list_processing})


@app.route("/program/list/", methods=['POST'])
def program_list_ajax():
    data = dict(request.form)
    term = data.get('term')
    if term:
        programs = program_repository.find_by_term(term)
    else:
        programs = program_repository.find_all()

    result = [{'id': program.id, 'text': program.title} for program in programs]
    return json.dumps({'results': result})


@app.route("/channel/list/", methods=['POST'])
def channel_list_ajax():
    data = dict(request.form)
    term = data.get('term')
    if term:
        channels = channel_repository.find_by_term(term)
    else:
        channels = channel_repository.find_all()

    result = [{'id': channel.id, 'text': channel.title} for channel in channels]

    return json.dumps({'results': result})


@app.route("/file/list/", methods=['POST'])
def file_list_ajax():
    data = dict(request.form)
    term = data.get('term')
    files = device.file_list
    if term:
        result = [{'id': file.md5, 'text': file.filename} for i, (cle, file) in enumerate(device.file_list.items())
                  if re.search(term, file.filename)]
    else:
        result = [{'id': file.md5, 'text': file.filename} for i, (md5, file) in enumerate(files.items())]

    return json.dumps({'results': result})


@app.route("/processing")
def is_processing():
    return jsonify(1)

def filter_var(var, type_filter):
    if type_filter == 'bool':
        if var in ['true', 'True', '1', 1, True, 'on']:
            return True
        else:
            return False


if __name__ == "__main__":
    app.run(host='0.0.0', port=5000, debug=True, use_reloader=False)

