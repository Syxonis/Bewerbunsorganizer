# Arbeitsagentur Job Tracker

This is a desktop tool I built to help manage job applications in a more organized way. It connects to the official API of the German Federal Employment Agency (Arbeitsagentur) and allows you to search for jobs, save listings, add personal notes, and track your application status.

## Features

- Job search by title, location, field, and job type (e.g. full-time, internship, training)
- Save job listings with status and personal notes
- Track status: New, Interested, Applied, Interview, Rejected, Accepted
- Direct link to the original listing on arbeitsagentur.de
- Export all saved jobs to a CSV file

## Requirements

- Python 3
- The following Python packages: `PyQt5`, `requests`

## How to Install

### 1. Install Python 3

If you haven’t already, download and install Python 3 from:

https://www.python.org/downloads/

Make sure to check the box that says **"Add Python to PATH"** during installation (especially on Windows).

### 2. Download the project

Either Download the release, and extract it to a folder,
OR
Open a terminal (or command prompt), then run:

```bash
git clone https://github.com/your-username/arbeitsagentur-job-tracker.git
```

### 3. Install dependencies

Open the Windows Terminal in the folder you just extracted, or open the Terminal and navigate to the folder, and type:
```bash
pip install -r requirements.txt
```

### 4. Run the program

Run the program normally
OR
```bash
python main.py
```

## How to Use

- Fill in the search form with job title, location, and optional filters.
- Click "Search" to load results.
- Select a job from the list and fill in notes or change its status.
- Click "Save Job" to store it.
- All saved jobs appear in the lower table and can be updated or deleted.
- Use "Export to CSV" to save your jobs in a spreadsheet-friendly format.

## Files in the Project

- `main.py` – Main application
- `job_data.py` – Handles reading/writing saved jobs
- `saved_jobs/` – Folder where job data is stored
- `requirements.txt` – Python dependencies

## Notes

This was built for personal use to keep track of job applications. If it’s useful for others, feel free to use or improve it.
