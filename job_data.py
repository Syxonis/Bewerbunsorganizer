# job_data.py
# Handles loading and saving of saved job entries to a local JSON file

import os
import json

SAVE_DIR = "saved_jobs"
SAVE_FILE = os.path.join(SAVE_DIR, "saved_jobs.json")

def load_jobs():
    """Load saved jobs from JSON file."""
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def save_jobs(jobs):
    """Save job entries to JSON file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Fehler beim Speichern der Datei: {e}")
