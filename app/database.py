"""
Database manager for ResumeMatch AI using SQLite.
Stores resumes, job descriptions, match results, interview sessions, and reports.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import DATABASE_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table (for current guest or future auth)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT,
        created_at TEXT
    )
    """)

    # 2. Analyses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        resume_filename TEXT,
        resume_raw TEXT,
        resume_parsed TEXT,
        jd_filename TEXT,
        jd_raw TEXT,
        jd_parsed TEXT,
        match_result TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 3. Interview Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id TEXT PRIMARY KEY,
        analysis_id TEXT,
        questions TEXT,
        answers TEXT,
        current_index INTEGER DEFAULT 0,
        is_completed INTEGER DEFAULT 0,
        average_score REAL DEFAULT 0.0,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
    )
    """)

    # 4. Preparation Reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preparation_reports (
        id TEXT PRIMARY KEY,
        analysis_id TEXT UNIQUE,
        report_data TEXT,
        created_at TEXT,
        FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
    )
    """)

    # Create default demo user if not exists
    cursor.execute("SELECT id FROM users WHERE id = 'default_user'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, email, name, created_at) VALUES (?, ?, ?, ?)",
            ('default_user', 'demo.user@resumematch.ai', 'Guest Candidate', datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

# Helper CRUD functions

def create_analysis(
    user_id: str = "default_user",
    title: str = "New Analysis",
    resume_raw: str = "",
    resume_filename: str = "",
    jd_raw: str = "",
    jd_filename: str = ""
) -> str:
    analysis_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO analyses (id, user_id, title, resume_filename, resume_raw, jd_filename, jd_raw, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (analysis_id, user_id, title, resume_filename, resume_raw, jd_filename, jd_raw, now, now))
    conn.commit()
    conn.close()
    return analysis_id

def update_analysis(analysis_id: str, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    for k, v in kwargs.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        updates.append(f"{k} = ?")
        params.append(v)
    
    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(analysis_id)

    query = f"UPDATE analyses SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    data = dict(row)
    for field in ['resume_parsed', 'jd_parsed', 'match_result']:
        if data.get(field):
            try:
                data[field] = json.loads(data[field])
            except Exception:
                pass
    return data

def list_analyses(user_id: str = "default_user") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, title, resume_filename, jd_filename, created_at, updated_at, match_result
    FROM analyses
    WHERE user_id = ?
    ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get('match_result'):
            try:
                item['match_result'] = json.loads(item['match_result'])
            except Exception:
                item['match_result'] = None
        results.append(item)
    return results

def delete_analysis(analysis_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Interview session functions

def save_interview_session(session_data: Dict[str, Any]) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    session_id = session_data["id"]
    
    cursor.execute("""
    INSERT OR REPLACE INTO interview_sessions 
    (id, analysis_id, questions, answers, current_index, is_completed, average_score, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        session_data.get("analysis_id"),
        json.dumps(session_data.get("questions", [])),
        json.dumps(session_data.get("answers", {})),
        session_data.get("current_index", 0),
        1 if session_data.get("is_completed") else 0,
        session_data.get("average_interview_score", 0.0),
        session_data.get("created_at", now),
        now
    ))
    conn.commit()
    conn.close()
    return session_id

def get_interview_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interview_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["questions"] = json.loads(data["questions"]) if data.get("questions") else []
    data["answers"] = json.loads(data["answers"]) if data.get("answers") else {}
    data["is_completed"] = bool(data["is_completed"])
    return data

def get_interview_session_by_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interview_sessions WHERE analysis_id = ? ORDER BY created_at DESC LIMIT 1", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["questions"] = json.loads(data["questions"]) if data.get("questions") else []
    data["answers"] = json.loads(data["answers"]) if data.get("answers") else {}
    data["is_completed"] = bool(data["is_completed"])
    return data

# Preparation reports functions

def save_preparation_report(analysis_id: str, report_data: Dict[str, Any]) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    report_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT OR REPLACE INTO preparation_reports (id, analysis_id, report_data, created_at)
    VALUES (?, ?, ?, ?)
    """, (report_id, analysis_id, json.dumps(report_data), now))
    conn.commit()
    conn.close()
    return report_id

def get_preparation_report(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM preparation_reports WHERE analysis_id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["report_data"] = json.loads(data["report_data"]) if data.get("report_data") else {}
    return data["report_data"]

# Initialize db at startup
init_db()
