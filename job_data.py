# job_data.py

import os, json

SAVE_DIR = "saved_jobs"
SAVE_FILE = os.path.join(SAVE_DIR, "saved_jobs.json")

def load_jobs():
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jobs(jobs):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
