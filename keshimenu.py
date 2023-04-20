import argparse
import configparser
import logging
import os
import signal
import subprocess
import sys
import time

import matplotlib.pyplot as plt
import pandas as pd
import netifaces
import curses

BANNER = r"""
   _____                       _____       _         _____          
  / ____|                     / ____|     | |       / ____|         
 | |  __  __ _ _ __ ___   ___| |     _ __ | |_ ___| |     ___  _ __ 
 | | |_ |/ _` | '_ ` _ \ / _ \ |    | '_ \| __/ _ \ |    / _ \| '__|
 | |__| | (_| | | | | | |  __/ |____| | | | ||  __/ |___| (_) | |   
  \_____|\__,_|_| |_| |_|\___|\_____|_| |_|\__\___|\_____\___/|_|   
"""

def print_banner():
    """Print the banner."""
    print(BANNER)

def signal_handler(signal, frame):
    """Handle CTRL-C signal to stop the access point and other tools."""
    logging.info('Exiting...')
    stop_ap()
    stop_airmon()
    stop_airodump()
    stop_mdk4()
    sys.exit(0)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Wireless hacking tool.')
    parser.add_argument('-c', '--config', help='path to config file', default='config.ini')
    parser.add_argument('-i', '--interface', help='wireless interface to use')
    parser.add_argument('-s', '--ssid', help='access point SSID')
    parser.add_argument('-p', '--password', help='access point password')
    parser.add_argument('-o', '--output', help='output file name')
    parser.add_argument('--channel', help='access point channel', type=int, default=1)
    parser.add_argument('--graph', help='generate signal strength graph', action='store_true')
    return parser.parse_args()


def parse_config(config_file):
    """Parse configuration file and return a dictionary."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['access_point']


def select_interface():
    """Prompt user to select a wireless interface."""
    interfaces = netifaces.interfaces()
    wireless_interfaces = [
        iface for iface in interfaces if iface.startswith('wlan')
    ]
    if not wireless_interfaces:
        print('No wireless interfaces found.')
        sys.exit(1)
    if len(wireless_interfaces) == 1:
        return wireless_interfaces[0]
    print('Select wireless interface:')
    for i, iface in enumerate(wireless_interfaces):
        print(f'{i+1}. {iface}')
    while True:
        selection = input('Enter selection: ')
        try:
            iface = wireless_interfaces[int(selection) - 1]
            return iface
        except (ValueError, IndexError):
            print('Invalid selection.')


def configure_access_point(config, iface):
    """Configure access point settings."""
    os.system(f'sudo ifconfig {iface} up')
    os.system(f'sudo ifconfig {iface} {config["ip_address"]}')
    os.system(f'sudo route add -net {config["subnet_mask"]} gw {config["gateway"]}')
    os.system(f'sudo service isc-dhcp-server restart')


def start_ap(config, iface):
    """Start access point using airbase-ng and hostapd."""
    logging.info('Starting access point...')
    os.system(f'sudo airmon-ng start {iface}')
    os.system(f'sudo