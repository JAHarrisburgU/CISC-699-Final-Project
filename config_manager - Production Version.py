#!/usr/bin/env python3
"""
Config Manager for Threat Harvester.

This module reads the 'config.ini' file to securely load
API credentials (api_id and api_hash) needed by the Telethon client.
"""

import configparser
import os
import sys

CONFIG_FILE = 'config.ini'

def load_config():
    """
    Loads API credentials from config.ini.

    If the file or keys are missing, it prints a clear error
    and exits the program, preventing the bot from running
    without proper configuration.
    
    :return: A tuple of (api_id, api_hash)
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"---")
        print(f"CRITICAL ERROR: Configuration file '{CONFIG_FILE}' not found.")
        print(f"Please create '{CONFIG_FILE}' in the same directory with your credentials.")
        print(f"---")
        print(f"Example content for {CONFIG_FILE}:\n")
        print(f"[telegram_api]")
        print(f"api_id = 12345678")
        print(f"api_hash = 0123456789abcdef0123456789abcdef")
        print(f"---")
        sys.exit(1) # Exit the program

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    try:
        # Use getint() for api_id as Telethon expects an integer
        api_id = config.getint('telegram_api', 'api_id')
        api_hash = config.get('telegram_api', 'api_hash')

        if not api_id or not api_hash:
            # This check is for empty values
            raise configparser.NoOptionError("api_id or api_hash is empty.", "telegram_api")

        return api_id, api_hash

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"---")
        print(f"CRITICAL ERROR: Config file '{CONFIG_FILE}' is improperly configured.")
        print(f"It must contain a [telegram_api] section with both 'api_id' and 'api_hash'.")
        print(f"Error details: {e}")
        print(f"---")
        sys.exit(1)

if __name__ == '__main__':
    # You can run this file directly (python3 config_manager.py) to test it
    print("Testing config loader...")
    api_id, api_hash = load_config()
    print(f"Successfully loaded API_ID: {api_id}")
    print(f"Successfully loaded API_HASH: {'*' * len(api_hash)}")