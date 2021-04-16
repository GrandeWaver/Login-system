import sqlite3
import config

connection = sqlite3.connect(config.DB_FILE)

cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS account
    (
        id INTEGER PRIMARY KEY,
        nickname NOT NULL UNIQUE,
        username NOT NULL UNIQUE,
        password NOT NULL,
        code
        
    )
""")

connection.commit()
