from os import path
import inspect
import sys

BASE_DIR = path.dirname(path.abspath(inspect.getfile(inspect.currentframe())))
DATA_DIR = '.data'
VAR_DIR = 'var'
APP_DIR = 'app'
VERSION_DIR = 'version'
NETWORK_DIR = path.join(BASE_DIR, 'network')
WPA_SUPPLICANT_DIR = path.join(BASE_DIR, 'wpa_supplicant')
NETWORK_INTERFACE_FILE = 'interfaces'
WPA_SUPPLICANT_FILE = 'wpa_supplicant.conf'
