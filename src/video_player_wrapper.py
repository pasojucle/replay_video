import os
from omxplayer.player import OMXPlayer
from pathlib import Path
import logging
from pprint import pprint

from file import File
from video import Video


class VideoPlayer:
    def __init__(self):
        self.players = {}

    def pause(self, video):
        if self.get_player(video):
            self.get_player(video).pause()
            return True

        return False

    def play(self, video):
        if self.get_player(video):
            self.get_player(video).play()
            return True
        else:
            return self.set_player(video)

    def quit(self, video):
        if self.get_player(video):
            self.get_player(video).quit()
            del self.players[video.id]
            return True

        return False

    def get_player(self, video):
        return self.players.get(video.id)

    def set_player(self, video):
        try:
            video_path = Path(File(video.filename).video)
            player_log = logging.getLogger(f"Player {video.id}")
            dbus_name = f'org.mpris.MediaPlayer2.omxplayer{video.id}'
            pprint(dbus_name)
            player = OMXPlayer(video_path, dbus_name=dbus_name)
            self.players.update({video.id: player})

            player.playEvent += lambda _: player_log.info("Play")
            player.pauseEvent += lambda _: player_log.info("Pause")
            player.stopEvent += lambda _: player_log.info("Stop")
        except Exception as err:
            print("****** ERROR: ******", str(err))
            return False




