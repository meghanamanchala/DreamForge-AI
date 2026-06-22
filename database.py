import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dreamforge.db")

def get_db_connection():
    """Establishes connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        idea TEXT NOT NULL,
        target_market TEXT,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Blueprints table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blueprints (
        session_id TEXT PRIMARY KEY,
        content TEXT NOT NULL,  -- JSON string of complete sections
        finalized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    )
    """)
    
    # 3. Agent Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        step_name TEXT NOT NULL,
        thoughts TEXT,
        output TEXT,
        tokens_used INTEGER DEFAULT 0,
        latency_ms INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    )
    """)

    # Migrations for existing databases
    try:
        cursor.execute("ALTER TABLE agent_logs ADD COLUMN tokens_used INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE agent_logs ADD COLUMN latency_ms INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def save_session(session_id, idea, target_market, status="started"):
    """Saves a new session or updates its status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sessions (id, idea, target_market, status)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        status = excluded.status
    """, (session_id, idea, target_market, status))
    conn.commit()
    conn.close()

def update_session_status(session_id, status):
    """Updates the status of a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", (status, session_id))
    conn.commit()
    conn.close()

def get_session(session_id):
    """Retrieves session information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_agent_log(session_id, agent_name, step_name, thoughts, output="", tokens_used=0, latency_ms=0):
    """Inserts a new trace log for an agent execution step."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO agent_logs (session_id, agent_name, step_name, thoughts, output, tokens_used, latency_ms)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, agent_name, step_name, thoughts, output, tokens_used, latency_ms))
    conn.commit()
    conn.close()

def get_agent_logs(session_id):
    """Gets all logs for a given session sorted chronologically."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT agent_name, step_name, thoughts, output, tokens_used, latency_ms, timestamp 
    FROM agent_logs 
    WHERE session_id = ? 
    ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_blueprint(session_id, content_dict):
    """Saves the completed startup blueprint."""
    conn = get_db_connection()
    cursor = conn.cursor()
    content_str = json.dumps(content_dict)
    cursor.execute("""
    INSERT INTO blueprints (session_id, content)
    VALUES (?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
        content = excluded.content,
        finalized_at = CURRENT_TIMESTAMP
    """, (session_id, content_str))
    conn.commit()
    conn.close()

def get_blueprint(session_id):
    """Retrieves a finalized blueprint."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM blueprints WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row['content']) if row else None

def get_all_sessions():
    """Retrieves all sessions from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_session(session_id):
    """Deletes a session and all its associated logs/blueprints (CASCADE)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Enable foreign key support so CASCADE works in SQLite
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def delete_all_sessions():
    """Deletes ALL sessions and cascaded data from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

# Initialize on import
init_db()
