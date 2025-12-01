#!/usr/bin/env python3
"""
Threat Harvester - A multi-bot controller for gathering threat intelligence.

This script serves as the master controller for deploying and managing a fleet of
Telegram bots (harvesters). It reads a list of bot tokens, initializes a
database for tracking, and launches a separate monitoring process for each bot.

The primary goal is to produce structured, machine-readable logs (JSON)
that can be easily ingested and analyzed by a SIEM platform like Splunk.
"""
import subprocess
import sys
import time
import datetime
import json
from colorama import Fore, Style, init

# Local module imports
import config_manager  # <-- CHANGED: Replaced api_checker
from database_manager import DatabaseManager

# Initialize colorama for cross-platform colored text
init()

HEADER_ART = r'''
████████╗██╗  ██╗██████╗ ███████╗ █████╗ ████████╗     ██╗  ██╗ █████╗ ██╗   ██╗███████╗███████╗███████╗
╚══██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝     ██║  ██║██╔══██╗██║   ██║██╔════╝██╔════╝██╔════╝
   ██║   ███████║██████╔╝█████╗  ███████║   ██║        ███████║███████║██║   ██║█████╗  █████╗  █████╗
   ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║   ██║        ██╔══██║██╔══██║██║   ██║██╔══╝  ╚════╝  ██╔══╝
   ██║   ██║  ██║██║  ██║███████╗██║  ██║   ██║        ██║  ██║██║  ██║╚██████╔╝███████╗███████╗███████╗
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝
   -- Open-Source Phishing Intelligence Gathering Framework --
'''

COMPLETION_MESSAGE = r'''
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   DEPLOYMENT COMPLETE: All harvester bots are active.    ║
║   System is now in persistent monitoring mode.           ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   > Structured logs are being written to:                ║
║     harvester_events.log                                 ║
║                                                          ║
║   > This terminal must remain open.                      ║
║   > Use your Splunk instance to monitor the log file.    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
'''

def write_log(log_data):
    """Appends a structured JSON log entry to the event file."""
    with open("harvester_events.log", "a") as log_file:
        log_file.write(json.dumps(log_data) + "\n")

def launch_harvesters(bot_token_file, db_manager):
    """
    Reads bot tokens and launches a dedicated monitor process for each.
    """
    # Log the session start
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"\n{Fore.CYAN}New harvesting session initiated at {start_time}{Style.RESET_ALL}")
    write_log({"event_type": "session_start", "timestamp": start_time, "status": "success"})

    try:
        with open(bot_token_file, "r") as tokens_file:
            bot_tokens = [line.strip() for line in tokens_file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}Error: The token file '{bot_token_file}' was not found.{Style.RESET_ALL}")
        write_log({"event_type": "session_start", "timestamp": start_time, "status": "failure", "reason": f"File not found: {bot_token_file}"})
        sys.exit(1)
    
    # --- NEW: Clear the database at the start of the session ---
    print(f"{Fore.CYAN}[*] Clearing previous bot registrations...{Style.RESET_ALL}")
    db_manager.clear_bots_table()
    # -----------------------------------------------------------

    bot_count = len(bot_tokens)
    print(f"{Fore.GREEN}[+] Processing {bot_count} bot tokens...{Style.RESET_ALL}")
    time.sleep(2)

    # Determine correct python executable based on OS
    python_executable = "python3" if sys.platform.startswith('linux') else "python"

    launched_count = 0
    for i, token in enumerate(bot_tokens, 1):
        # The bot_id is now just the simple number. 
        # The bot_monitor script will add the 'harvester-' prefix.
        bot_id = str(i) # <-- CHANGED: Simplified bot_id
        
        print(f"  -> Deploying harvester-{i:03d}...")
        try:
            # Add bot to the database before launching
            # We use the full "harvester-001" name for the database key
            db_manager.add_bot(f"harvester-{i:03d}", token)

            # Launch the bot monitor script as a separate process
            # We pass the simplified ID (e.g., "1") and the token
            subprocess.Popen([python_executable, 'bot_monitor.py', token, bot_id])

            write_log({
                "event_type": "harvester_launch",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "bot_id": f"harvester-{i:03d}",
                "status": "success"
            })
            launched_count += 1
            time.sleep(1) # Stagger the launches slightly
        except Exception as e:
            print(f"{Fore.RED}  -> Failed to deploy harvester-{i:03d}: {e}{Style.RESET_ALL}")
            write_log({
                "event_type": "harvester_launch",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "bot_id": f"harvester-{i:03d}",
                "status": "failure",
                "reason": str(e)
            })

    time.sleep(3)
    print(f"\n{Fore.YELLOW}{COMPLETION_MESSAGE}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}Successfully launched {launched_count} out of {bot_count} harvesters.{Style.RESET_ALL}\n")

def main():
    """
    Main function to orchestrate the application setup and launch.
    """
    if len(sys.argv) < 2:
        print(f"\nUsage: {sys.argv[0]} <bot_token_file>")
        print("  Example: python3 threat_harvester.py tokens.txt\n")
        sys.exit(1)

    # Get the token file path from the command line argument
    bot_token_file = sys.argv[1]

    print(f"{Fore.CYAN}{HEADER_ART}{Style.RESET_ALL}")
    print("Initializing Threat Harvester...")
    time.sleep(1)

    # --- Pre-Launch Checks ---
    print("[*] Performing pre-launch checks...")

    # --- CHANGED: Use config_manager to check config.ini ---
    # 1. Check for config.ini and API keys
    try:
        config_manager.load_config()
        print(f"{Fore.GREEN}[+] API configuration (config.ini)... OK{Style.RESET_ALL}")
    except SystemExit:
        # config_manager.load_config() prints its own error and calls sys.exit(1)
        # This 'except' just ensures we catch the exit signal gracefully.
        print(f"{Fore.RED}Critical Error: Please fix config.ini before proceeding.{Style.RESET_ALL}")
        sys.exit(1)
    # -----------------------------------------------------

    # 2. Initialize Database
    try:
        # We now use the default DB name "harvester_db.sqlite"
        db_manager = DatabaseManager()
        db_manager.create_tables()
        print(f"{Fore.GREEN}[+] Database connection... OK{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Critical Error: Could not initialize database: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # --- Launch Sequence ---
    launch_harvesters(bot_token_file, db_manager)

    # Keep the main controller script alive
    # This is crucial so the subprocesses aren't orphaned
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Shutdown signal received. Terminating harvester controller.{Style.RESET_ALL}")
        # In a real app, you'd signal the child processes to shut down gracefully here.
        sys.exit(0)

if __name__ == "__main__":
    main()