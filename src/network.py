#!/usr/bin/env python
# -*- coding: utf8 -*-

from os import path, remove
from time import sleep
import re
from pprint import pprint

import shutil
import logging
from log_gen import LogGen
import subprocess
from collections import UserDict

import requests
import config

NETWORK_INTERFACE_FILE = 'interfaces'

CONNECTION_CABLE = 0
CONNECTION_WIFI = 1
CONNECTION_WIFI_HIDE = 2
PROTOCOL_DHCP = 0
PROTOCOL_IP_FIXED = 1
INDENT = '    '
SSID_PI = 'Raspberry'
PSK_PI = 'Raspberry'

logger = LogGen().loggen()

class Network(UserDict):

    def __init__(self, *args, **kwargs):
        UserDict.__init__(self, *args, **kwargs)
        self.network_interface_file = self.get_networkinterfacefile()
        self.wpa_supplicant_file = self.get_wpasupplicantfile()
        self.connection = None
        self.id_str = None
        self.ssid = None
        self.psk = None
        self.address = None
        self.netmask = None
        self.gateway = None
        self.dns_nameservers = None
        self.dhcp = True
        self.dns = True

    def __str__(self):
        return f"ssid: {self.ssid}, psk: {self.psk}, id_str: {self.id_str}, address: {self.address}, netmask: {self.netmask}, gateway: {self.gateway}, dns_nameservers: {self.dns_nameservers}"

    def save(self):
        logger.info('Network settings backup')
        if path.isfile(self.network_interface_file):
            shutil.copy2(self.network_interface_file, self.network_interface_file + ".bak")
        if path.isfile(self.wpa_supplicant_file):
            shutil.copy2(self.wpa_supplicant_file, self.wpa_supplicant_file + ".bak")

    def backup(self):
        if path.isfile(self.network_interface_file + ".bak"):
            logger.info('Restore network interface backup')
            shutil.copy2(self.network_interface_file + ".bak", self.network_interface_file)
            remove(self.network_interface_file + ".bak")
        if path.isfile(self.wpa_supplicant_file + ".bak"):
            logger.info('Restore wpa supplicant backup')
            shutil.copy2(self.wpa_supplicant_file + ".bak", self.wpa_supplicant_file)
            remove(self.wpa_supplicant_file + ".bak")
        self.relod_network_interface()

    def parse(self, data):
        self.id_str = data.get('id_str')
        self.ssid = data.get('ssid')
        self.psk = data.get('psk')
        self.address = data.get('address')
        self.netmask = data.get('netmask')
        self.gateway = data.get('gateway')
        self.dns_nameservers = data.get('dns_nameservers')
        self.dhcp = self.get_dhcp()
        self.dns = self.get_dns()

    def get_dhcp(self):
        if self.address and self.netmask and self.gateway:
            return False

        return True

    def get_dns(self):
        if self.dns_nameservers:
            return False

        return True

    def set_wifi(self, data):
        self.parse(data)
        network_interface = ["auto lo",
                             "{}iface lo inet loopback".format(INDENT), "",
                             "auto eth0",
                             "{}iface eth0 inet dhcp".format(INDENT)]

        if data.get('ssid') is None or data.get('psk') is None:
            return False
        network_interface.extend(["", "allow-hotplug wlan0", "iface wlan0 inet manual",
                                  "wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf"])

        if self.dhcp:
            network_interface.extend(["", "iface prioritaire inet dhcp"])
        else:
            network_interface.extend(["", "iface prioritaire inet static".format(INDENT)])
            network_interface.extend(self.get_routes())

        if bool(self.dns_nameservers):
            network_interface.extend(self.get_dns_nameserveur())

        wpa_supplicant = self.get_wpa_supplicant()

        with open(self.wpa_supplicant_file, "w") as f:
            wpa_supplicant_content = "\n".join(wpa_supplicant)
            f.write(wpa_supplicant_content)

        with open(self.network_interface_file, "w") as f:
            network_interface_content = "\n".join(network_interface)
            f.write(network_interface_content)
        return True

        return False

    def get_wifi(self):
        wifi_files_conf = {
            self.wpa_supplicant_file: r'(ssid|psk|id_str)="(.+)"',
            self.network_interface_file: r'(ssid|psk|id_str|address|netmask|gateway|dns-nameservers)\s(.+)'
        }
        for i, (file, pattern) in enumerate(wifi_files_conf.items()):
            with open(file, "r") as f:
                content = f.read()
                for line in content.split('\n'):
                    match = re.match(pattern, line.strip())
                    if match:
                        setattr(self, match.group(1).replace('-', '_'), match.group(2))

        self.dhcp = self.get_dhcp()

        return self

    @staticmethod
    def get_networkinterfacefile():
        return path.join(config.NETWORK_DIR, NETWORK_INTERFACE_FILE)

    @staticmethod
    def get_wpasupplicantfile():
        return path.join(config.WPA_SUPPLICANT_DIR, config.WPA_SUPPLICANT_FILE)

    @staticmethod
    def reload_network_interface():
        subprocess.call(['ifdown', 'eth0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(['ifdown', '--force', 'wlan0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sleep(5)
        subprocess.call(['service', 'networking', 'restart'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sleep(5)
        subprocess.call(['ifup', 'eth0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(['ifup', 'wlan0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_routes(self):
        routes = []
        routes.append("{0}address {1}".format(INDENT, self.address))
        routes.append("{0}netmask {1}".format(INDENT, self.netmask))
        routes.append("{0}gateway {1}".format(INDENT, self.gateway))

        return routes

    def get_dns_nameserveur(self):
        return "{0}dns-nameservers {1}".format(INDENT, self.dns_nameservers)


    def get_wpa_supplicant(self):
        wpa_supplicant = ['ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev ',
                          'update_config=1',
                          'country=FR']

        wpa_supplicant.extend(['network={',
                               '{}scan_ssid=1'.format(INDENT),
                               '{0}ssid="{1}"'.format(INDENT, self.ssid),
                               '{0}psk="{1}"'.format(INDENT, self.psk),
                               '{0}id_str="prioritaire"'.format(INDENT),
                               '}'])

        return wpa_supplicant

    @staticmethod
    def get_ip_config():
        interfaces = ['eth0', 'wlan0']
        ips = {}
        for interface in interfaces:
            if not network.is_connect_eth0() and 'eth0' == interface:
                interface_ip = None
            else:
                try:
                    bash_command = f"ifconfig {interface} | awk '/inet /{{print substr($2,1)}}'"
                    result = subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)
                    interface_ip = result.stdout
                except subprocess.CalledProcessError as e:
                    interface_ip = None
            ips.update({interface: interface_ip})

        return ips

    @staticmethod
    def is_connect_eth0():
        try:
            bash_command = 'cat /sys/class/net/eth0/carrier'
            result = subprocess.run(['bash', '-c', bash_command], capture_output=True, text=True, check=True)
            is_connect = int(re.match(r'^(\d{1})\s$', result.stdout)[1])
        except subprocess.CalledProcessError as e:
            is_connect = False

        return bool(is_connect)


network = Network()
