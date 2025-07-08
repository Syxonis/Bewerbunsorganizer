import os
import requests
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from job_data import load_jobs, save_jobs
from functools import partial


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbeitsagentur Job Tracker")
        self.resize(1680, 1080)

        self.search_results = []
        self.saved_jobs = load_jobs()

        # --- Central Layout ---
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # --- Search Input ---
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Berufsfeld (z.B. Informatik)")

        self.offer_type_input = QtWidgets.QComboBox()
        self.offer_type_input.addItem("Alle", "")  # leer bedeutet kein Filter
        self.offer_type_input.addItem("Arbeit", "1")
        self.offer_type_input.addItem("Selbstständigkeit", "2")
        self.offer_type_input.addItem("Ausbildung/Duales Studium", "4")
        self.offer_type_input.addItem("Praktikum/Trainee", "34")

        search_layout = QtWidgets.QHBoxLayout()
        self.input_title = QtWidgets.QLineEdit()
        self.input_title.setPlaceholderText("Was (Jobtitel)")
        self.input_location = QtWidgets.QLineEdit()
        self.input_location.setPlaceholderText("Wo (Ort)")
        self.search_button = QtWidgets.QPushButton("Search")
        search_layout.addWidget(self.input_title)
        search_layout.addWidget(self.input_location)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.input_field)
        search_layout.addWidget(self.offer_type_input)
        layout.addLayout(search_layout)

        # --- Results Table ---
        self.results_table = QtWidgets.QTableWidget(0, 7)
        self.results_table.setHorizontalHeaderLabels([
            "Title", "Company", "Location", "Art", "RefNr", "Link", "Speichern"
        ])
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(QtWidgets.QLabel("Suchergebnisse:"))
        layout.addWidget(self.results_table)

        # --- Detail & Save ---
        self.active_saved_row = None
        self.detail_box = QtWidgets.QGroupBox("Details speichern")
        detail_form = QtWidgets.QFormLayout(self.detail_box)
        self.label_title = QtWidgets.QLabel("")
        self.label_company = QtWidgets.QLabel("")
        self.label_location = QtWidgets.QLabel("")
        self.label_refnr = QtWidgets.QLabel("")
        self.link_button = QtWidgets.QPushButton("Zur Anzeige")
        self.link_button.clicked.connect(self.open_job_link)
        self.current_link = ""
        self.note_input = QtWidgets.QTextEdit()
        self.status_input = QtWidgets.QComboBox()
        self.status_input.addItems(["New", "Interested", "Applied", "Interview", "Rejected", "Accepted"])
        self.save_button = QtWidgets.QPushButton("Save Job")
        detail_form.addRow("Title:", self.label_title)
        detail_form.addRow("Company:", self.label_company)
        detail_form.addRow("Location:", self.label_location)
        detail_form.addRow("Status:", self.status_input)
        detail_form.addRow("Notes:", self.note_input)
        detail_form.addRow("RefNr:", self.label_refnr)
        detail_form.addRow("Link:", self.link_button)
        detail_form.addRow(self.save_button)
        self.detail_box.hide()
        layout.addWidget(self.detail_box)

        # --- Saved Jobs Table ---
        self.saved_table = QtWidgets.QTableWidget(0, 8)
        self.saved_table.setHorizontalHeaderLabels(
            ["Title", "Company", "Location", "Status", "Notes", "RefNr", "Link", "Löschen"])
        layout.addWidget(QtWidgets.QLabel("Gespeicherte Jobs:"))
        layout.addWidget(self.saved_table)

        # --- Connections ---
        self.search_button.clicked.connect(self.search_jobs)
        self.results_table.itemSelectionChanged.connect(self.show_detail_panel)
        self.saved_table.cellClicked.connect(self.show_saved_detail)
        self.save_button.clicked.connect(self.save_job)
        self.saved_table.itemChanged.connect(self.update_saved_note)

        self.load_saved_table()

    def search_jobs(self):
        if not self.input_location.text().strip():
            QtWidgets.QMessageBox.warning(self, "Fehler", "Bitte gib mindestens einen Ort an.")
            return

        self.results_table.setRowCount(0)
        self.search_results = []

        url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
        headers = {"X-API-Key": "jobboerse-jobsuche"}
        params = {
            "wo": self.input_location.text().strip(),
            "was": self.input_title.text().strip(),
            "berufsfeld": self.input_field.text().strip(),
            "angebotsart": self.offer_type_input.currentData(),
            "size": 25,
        }
        params = {k: v for k, v in params.items() if v}

        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            jobs = res.json().get("stellenangebote", [])
            if jobs:
                print(json.dumps(jobs[0], indent=2, ensure_ascii=False))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"API error:\n{e}")
            return

        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Title", "Company", "Location", "Art", "RefNr", "Link", "Speichern"
        ])

        for row, job in enumerate(jobs):
            title = str(job.get("titel") or "N/A")
            company = str(job.get("arbeitgeber") or "N/A")

            location_data = job.get("arbeitsort") or {}
            location = f"{location_data.get('region', '')}, {location_data.get('ort', '')}".strip(', ')

            angebotsart_raw = job.get("angebotsart", "")
            angebotsart_map = {
                "1": "Arbeit",
                "2": "Selbstständigkeit",
                "4": "Ausbildung",
                "34": "Praktikum"
            }
            angebotsart = angebotsart_map.get(str(angebotsart_raw), "Unbekannt")

            refnr = job.get("refnr", "N/A")
            link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

            self.search_results.append(job)

            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(title))
            self.results_table.setItem(row, 1, QtWidgets.QTableWidgetItem(company))
            self.results_table.setItem(row, 2, QtWidgets.QTableWidgetItem(location))
            self.results_table.setItem(row, 3, QtWidgets.QTableWidgetItem(angebotsart))
            self.results_table.setItem(row, 4, QtWidgets.QTableWidgetItem(refnr))

            link_button = QtWidgets.QPushButton("Zur Anzeige")
            link_button.clicked.connect(lambda _, url=link: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
            self.results_table.setCellWidget(row, 5, link_button)

            save_button = QtWidgets.QPushButton("Speichern")
            save_button.clicked.connect(lambda _, r=row: self.save_job(r))
            self.results_table.setCellWidget(row, 6, save_button)

        self.results_table.resizeColumnsToContents()

    def show_saved_detail(self, row, column):
        if row < 0 or row >= len(self.saved_jobs):
            return
        job = self.saved_jobs[row]

        self.label_title.setText(job["title"])
        self.label_company.setText(job["company"])
        self.label_location.setText(job["location"])
        self.status_input.setCurrentText(job["status"])
        self.note_input.setText(job["notes"])
        refnr = job.get("refnr", "N/A") if isinstance(job, dict) else "N/A"
        link = job.get("link", "") if isinstance(job, dict) else ""

        self.label_refnr.setText(refnr)
        self.current_link = link

        self.detail_box.show()
        self.active_saved_row = row

    def show_detail_panel(self):
        row = self.results_table.currentRow()
        if row == -1:
            return

        job = self.search_results[row]
        self.label_title.setText(str(job.get("titel") or ""))
        self.label_company.setText(str(job.get("arbeitgeber") or ""))
        location_data = job.get("arbeitsort") or {}
        location = f"{location_data.get('region', '')}, {location_data.get('ort', '')}".strip(', ')
        self.label_location.setText(location)

        refnr = job.get("refnr", "N/A")
        link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}" if refnr != "N/A" else ""

        self.label_refnr.setText(refnr)
        self.current_link = link

        self.note_input.clear()
        self.status_input.setCurrentIndex(0)
        self.detail_box.show()

    def save_job(self, row=None):
        if self.active_saved_row is not None:
            self.saved_jobs[self.active_saved_row]["status"] = self.status_input.currentText()
            self.saved_jobs[self.active_saved_row]["notes"] = self.note_input.toPlainText()
            save_jobs(self.saved_jobs)
            self.refresh_saved_table()
            self.active_saved_row = None
            return

        if row is None:
            row = self.results_table.currentRow()
        if row < 0 or row >= len(self.search_results):
            return

        job = self.search_results[row]
        location_data = job.get("arbeitsort") or {}
        location = f"{location_data.get('region', '')}, {location_data.get('ort', '')}".strip(', ')

        entry = {
            "title": str(job.get("titel") or ""),
            "company": str(job.get("arbeitgeber") or ""),
            "location": location,
            "status": self.status_input.currentText(),
            "notes": self.note_input.toPlainText(),
            "refnr": job.get("refnr", "N/A"),
            "link": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{job.get('refnr', '')}"
        }

        for saved in self.saved_jobs:
            if saved["title"] == entry["title"] and saved["company"] == entry["company"]:
                QtWidgets.QMessageBox.warning(self, "Schon gespeichert", "Dieser Job wurde bereits gespeichert.")
                return

        self.saved_jobs.append(entry)
        self.add_saved_row(entry)
        save_jobs(self.saved_jobs)

    def add_saved_row(self, job):
        row = self.saved_table.rowCount()
        self.saved_table.insertRow(row)
        self.saved_table.setItem(row, 0, QtWidgets.QTableWidgetItem(job["title"]))
        self.saved_table.setItem(row, 1, QtWidgets.QTableWidgetItem(job["company"]))
        self.saved_table.setItem(row, 2, QtWidgets.QTableWidgetItem(job["location"]))

        # Status dropdown
        combo = QtWidgets.QComboBox()
        combo.addItems(["New", "Interested", "Applied", "Interview", "Rejected", "Accepted"])
        combo.setCurrentText(job["status"])
        combo.currentIndexChanged.connect(lambda _, r=row: self.update_saved_status(r))
        self.saved_table.setCellWidget(row, 3, combo)

        # Notes cell
        note_item = QtWidgets.QTableWidgetItem(job["notes"])
        note_item.setFlags(note_item.flags() | QtCore.Qt.ItemIsEditable)
        self.saved_table.setItem(row, 4, note_item)

        # RefNr
        self.saved_table.setItem(row, 5, QtWidgets.QTableWidgetItem(job.get("refnr", "N/A")))

        # Link Button
        link_btn = QtWidgets.QPushButton("Zur Anzeige")
        link_btn.clicked.connect(lambda _, url=job.get("link", ""): QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
        self.saved_table.setCellWidget(row, 6, link_btn)

        # Delete
        delete_button = QtWidgets.QPushButton("Löschen")
        delete_button.clicked.connect(partial(self.delete_saved_job, row))
        self.saved_table.setCellWidget(row, 7, delete_button)


        # Button cell
        delete_button = QtWidgets.QPushButton("Löschen")
        delete_button.clicked.connect(partial(self.delete_saved_job, row))

    def delete_saved_job(self, row):
        self.saved_table.removeRow(row)
        if 0 <= row < len(self.saved_jobs):
            del self.saved_jobs[row]
            save_jobs(self.saved_jobs)

    def update_saved_status(self, row):
        combo = self.saved_table.cellWidget(row, 3)
        if combo:
            self.saved_jobs[row]["status"] = combo.currentText()
            save_jobs(self.saved_jobs)

    def update_saved_note(self, item):
        row, col = item.row(), item.column()
        if col == 4:
            self.saved_jobs[row]["notes"] = item.text()
            save_jobs(self.saved_jobs)

    def open_job_link(self):
        if self.current_link:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.current_link))

    def load_saved_table(self):
        for job in self.saved_jobs:
            self.add_saved_row(job)

    def refresh_saved_table(self):
        self.saved_table.setRowCount(0)
        for job in self.saved_jobs:
            self.add_saved_row(job)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()
