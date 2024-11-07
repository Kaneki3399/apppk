import sqlite3


def create_database():
    conn = sqlite3.connect('myallfiles.db')
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_id TEXT UNIQUE,
            file_name TEXT,
            results TEXT,
            date_time TEXT,
            username TEXT
        )
    ''')

    conn.commit()
    conn.close()
