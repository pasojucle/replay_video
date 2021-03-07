import os
import inspect


BASE_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
DATA_BASE = 'database.db'
APP_DIR = 'app'
DEVICE = 'sdd1'
MEDIA_DIR = '/home/patrick/Vidéos'
VIDEOS_DIR = 'test_videos'
THUMBNAILS_DIR = 'thumbnails'
# NETWORK_DIR = '/etc/network'
# WPA_SUPPLICANT_DIR = '/etc/wpa_supplicant'
NETWORK_DIR = os.path.join(BASE_DIR, 'network')
WPA_SUPPLICANT_DIR = os.path.join(BASE_DIR, 'wpa_supplicant')
NETWORK_INTERFACE_FILE = 'interfaces'
WPA_SUPPLICANT_FILE = 'wpa_supplicant.conf'
