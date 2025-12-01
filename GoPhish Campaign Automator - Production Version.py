import json
import configparser
import sys
import time
from gophish import Gophish
from gophish.models import *

# --- CONFIGURATION ---

CONFIG_FILE = 'config.ini'

def load_gophish_config():
    """
    Loads GoPhish configuration from the [gophish] section
    of the config.ini file.
    """
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        print(f"[!] FATAL: Config file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    
    try:
        gophish_config = config['gophish']
        return {
            "api_key": gophish_config['gophish_api_key'],
            "url": gophish_config['gophish_url'],
            "verify_ssl": config.getboolean('gophish', 'gophish_verify_ssl', fallback=True),
            "log_file": config.get('gophish', 'harvester_log_file', fallback='harvester_events.log'),
            "campaign_group_name": gophish_config['campaign_group_name'],
            "campaign_template_name": gophish_config['campaign_template_name'],
            "campaign_smtp_name": gophish_config['campaign_smtp_name'],
            "campaign_listener_url": gophish_config['campaign_listener_url']
        }
    except KeyError as e:
        print(f"[!] FATAL: Missing key {e} in [gophish] section of '{CONFIG_FILE}'.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] FATAL: Error reading config file: {e}")
        sys.exit(1)

# --- HELPER FUNCTIONS ---

def read_latest_ioc(log_file="harvester_events.log"):
    """
    Reads the log file efficiently and returns the most recent 'phishing_url' IOC.
    """
    latest_url = None
    try:
        with open(log_file, "r") as f:
            # Read line-by-line to be memory-efficient.
            # The last one found will be the most recent.
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get("event_type") == "ioc_discovered":
                        data = log_entry.get("data", {})
                        if data.get("ioc_type") == "phishing_url":
                            latest_url = data.get("value")
                except json.JSONDecodeError:
                    continue # Skip corrupted log lines
            
    except FileNotFoundError:
        print(f"[!] Error: Log file '{log_file}' not found.")
        return None
    
    if latest_url:
        print(f"[+] Found most recent phishing URL IOC: {latest_url}")
        return latest_url
    else:
        print("[!] No phishing URL IOCs found in the log file.")
        return None

def find_by_name(items, name):
    """Helper to find an object in a list by its name."""
    for item in items:
        if item.name == name:
            return item
    return None

def find_or_create_template(api, name):
    """Finds a template by name or creates it if not found."""
    print(f"[*] Checking for existing template: '{name}'...")
    templates = api.templates.get()
    template = find_by_name(templates, name)
    
    if template:
        print(f"[+] Found existing template with ID: {template.id}")
        return template
    
    print(f"[-] No template found. Creating new one...")
    template_model = Template(
        name=name,
        subject='Action Required: Unusual Sign-in Activity',
        html='''
        <html>
        <body>
        <p>Hello {{.FirstName}},</p>
        <p>Our system detected a suspicious login attempt on your account.</p>
        <p>Please verify your recent activity by clicking the link below:</p>
        <p><a href="{{.URL}}">Verify My Account Activity</a></p>
        <p>If you do not recognize this activity, please reset your password immediately.</p>
        <p>Thank you,<br>IT Security Team</p>
        </body>
        </html>
        '''
    )
    template = api.templates.post(template_model)
    print(f"[+] New template '{template.name}' created with ID: {template.id}")
    return template

def find_or_create_page(api, phish_url):
    """Finds an imported page by name or creates it if not found."""
    page_name = f'Imported Site - {phish_url}'