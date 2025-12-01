#!/usr/bin/env python3
"""
DatabaseManager for the Threat Harvester project.

This class encapsulates all interactions with the SQLite database, providing a
clean, object-oriented interface for managing bot records. This approach
improves modularity and separates database concerns from the main application logic.
"""
import sqlite3
from sqlite3 import Error

class DatabaseManager:
    """Handles all database operations for harvester bots."""
    
    def __init__(self, db_file="harvester_db.sqlite"):
        """
        Initializes the DatabaseManager and connects to the database.
        
        :param db_file: Path to the SQLite database file.
        """
        self.db_file = db_file
        self.conn = self._create_connection()
        if not self.conn:
            print(f"Error! Cannot create the database connection to {self.db_file}")
            # In a real app, this should raise an exception
            raise sqlite3.Error(f"Could not connect to database: {self.db_file}")

    def _create_connection(self):
        """Creates and returns a database connection."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(f"Database connection error: {e}")
        return conn

    def create_tables(self):
        """Creates the 'bots' table if it doesn't already exist."""
        sql_create_bots_table = """
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id TEXT NOT NULL UNIQUE,
            bot_token TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            events_collected INTEGER DEFAULT 0
        );
        """
        try:
            c = self.conn.cursor()
            c.execute(sql_create_bots_table)
            self.conn.commit()
        except Error as e:
            print(f"Table creation error: {e}")

    def add_bot(self, bot_id, bot_token):
        """
        Adds a new bot record to the database.

        :param bot_id: A unique identifier for the bot (e.g., 'harvester-001').
        :param bot_token: The Telegram API token for the bot.
        :return: The ID of the newly inserted row, or None on failure.
        """
        sql = '''INSERT INTO bots(bot_id, bot_token) VALUES(?,?)'''
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (bot_id, bot_token))
            self.conn.commit()
            return cur.lastrowid
        except Error as e:
            print(f"Error adding bot {bot_id}: {e}")
            return None

    def clear_bots_table(self):
        """Deletes all records from the bots table for a clean session start."""
        sql = 'DELETE FROM bots'
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
        except Error as e:
            print(f"Error clearing bots table: {e}")

    def __del__(self):
        """Destructor to ensure the database connection is closed."""
        if self.conn:
            self.conn.close()