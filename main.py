import csv
import os
import requests
from PyQt5 import QtWidgets, QtCore, QtGui
from job_data import load_jobs, save_jobs  # Module to load and save job data

def is_valid_job(job):
    return bool(
        job and
        job.get("title") and
        job.get("company") and
        job.get("refnr") and
        isinstance(job.get("title"), str) and
        isinstance(job.get("company"), str)
    )

# Custom list widget for handling file drops
class FileListWidget(QtWidgets.QListWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Keep reference to main window for context
        # Enable dropping files onto this widget
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # Accept event if it contains URLs (files)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # Accept drag move events similarly
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Handle files dropped onto the list
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # If no job is currently selected (not saved), show warning
            if self.main_window.active_saved_row is None:
                QtWidgets.QMessageBox.warning(
                    self.main_window,
                    "Nicht gespeichert",
                    "Bitte speichere den Job, bevor Dateien hinzugefügt werden."
                )
                return
            # Add each dropped file to the current job
            urls = event.mimeData().urls()
            for url in urls:
                local_path = url.toLocalFile()
                if local_path:
                    self.main_window.add_file_to_current_job(local_path)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbeitsagentur Job Tracker")
        self.resize(1680, 1080)

        # Initialize data containers
        self.search_results = []
        self.saved_jobs = load_jobs()  # Load saved jobs from file
        self.active_saved_row = None
        self.current_link = ""

        # Install an event filter to detect clicks outside the detail panel
        QtWidgets.QApplication.instance().installEventFilter(self)

        self.init_ui()          # Set up UI components
        self.load_saved_table() # Populate the saved jobs table

    def init_ui(self):
        # Central widget and main layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # --- Search input fields ---
        self.input_title = QtWidgets.QLineEdit()
        self.input_title.setPlaceholderText("Was (Jobtitel)")
        self.input_location = QtWidgets.QLineEdit()
        self.input_location.setPlaceholderText("Wo (Ort)")
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Berufsfeld (z.B. Informatik)")

        # Dropdown for offer type selection
        self.offer_type_input = QtWidgets.QComboBox()
        self.offer_type_input.addItem("Alle", "")
        self.offer_type_input.addItem("Arbeit", "1")
        self.offer_type_input.addItem("Selbstständigkeit", "2")
        self.offer_type_input.addItem("Ausbildung/Duales Studium", "4")
        self.offer_type_input.addItem("Praktikum/Trainee", "34")

        self.search_button = QtWidgets.QPushButton("Search")

        # Layout the search bar
        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(self.input_title)
        search_layout.addWidget(self.input_location)
        search_layout.addWidget(self.input_field)

        # Label for offer type dropdown
        offer_type_label = QtWidgets.QLabel("Angebotsart:")
        search_layout.addWidget(offer_type_label)
        search_layout.addWidget(self.offer_type_input)

        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # --- Results table ---
        self.results_table = QtWidgets.QTableWidget(0, 7)
        self.results_table.setHorizontalHeaderLabels([
            "Title", "Details", "Company", "Location", "RefNr", "Link", "Speichern"
        ])
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.results_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(QtWidgets.QLabel("Suchergebnisse:"))

        # Filter field above results table
        self.results_filter = QtWidgets.QLineEdit()
        self.results_filter.setPlaceholderText("Filter Ergebnisse")
        layout.addWidget(self.results_filter)
        layout.addWidget(self.results_table)

        # --- Detail panel (initially hidden) ---
        self.detail_box = QtWidgets.QGroupBox()  # no title, add custom header
        self.detail_box.setVisible(False)
        detail_form = QtWidgets.QFormLayout(self.detail_box)

        # Header with title and close button in detail panel
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_label = QtWidgets.QLabel("Details speichern")
        self.close_detail_button = QtWidgets.QPushButton("X")
        self.close_detail_button.clicked.connect(self.close_detail_panel)
        self.close_detail_button.setFixedWidth(20)
        self.close_detail_button.setFixedHeight(20)
        self.close_detail_button.setStyleSheet("padding:0px; font-weight:bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_detail_button)
        detail_form.addRow(header_widget)

        # Detail fields (Title, Company, etc.)
        self.label_title = QtWidgets.QLabel()
        self.label_company = QtWidgets.QLabel()
        self.label_location = QtWidgets.QLabel()
        self.label_refnr = QtWidgets.QLabel()
        self.link_button = QtWidgets.QPushButton("Zur Anzeige")
        self.link_button.clicked.connect(self.open_job_link)
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

        # --- Files section in detail ---
        self.files_label = QtWidgets.QLabel("Files:")
        self.file_list_widget = FileListWidget(self)
        self.file_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.files_btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(self.files_btn_widget)
        self.add_file_btn = QtWidgets.QPushButton("Add File")
        self.open_file_btn = QtWidgets.QPushButton("Open File")
        self.remove_file_btn = QtWidgets.QPushButton("Remove File")
        btn_layout.addWidget(self.add_file_btn)
        btn_layout.addWidget(self.open_file_btn)
        btn_layout.addWidget(self.remove_file_btn)
        self.add_file_btn.clicked.connect(self.add_files_dialog)
        self.open_file_btn.clicked.connect(self.open_selected_file)
        self.remove_file_btn.clicked.connect(self.remove_selected_files)

        detail_form.addRow(self.files_label, self.file_list_widget)
        detail_form.addRow("", self.files_btn_widget)

        detail_form.addRow(self.save_button)
        self.detail_box.setLayout(detail_form)
        layout.addWidget(self.detail_box)

        # --- Saved jobs table ---
        self.saved_table = QtWidgets.QTableWidget(0, 10)
        self.saved_table.setHorizontalHeaderLabels([
            "Title", "Details", "Company", "Location",
            "Status", "Notes", "RefNr", "Link", "Dokumente", "Löschen"
        ])
        self.saved_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.saved_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.saved_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.saved_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(QtWidgets.QLabel("Gespeicherte Jobs:"))

        # Filter field above saved table
        self.saved_filter = QtWidgets.QLineEdit()
        self.saved_filter.setPlaceholderText("Filter gespeicherte Jobs")
        layout.addWidget(self.saved_filter)
        layout.addWidget(self.saved_table)

        # Export to CSV button
        self.export_button = QtWidgets.QPushButton("Export to CSV")
        layout.addWidget(self.export_button)

        # Connect signals for buttons and inputs
        self.search_button.clicked.connect(self.search_jobs)
        self.save_button.clicked.connect(self.save_job)
        self.saved_table.itemChanged.connect(self.update_saved_note)
        self.saved_filter.textChanged.connect(self.apply_saved_filter)
        self.results_filter.textChanged.connect(self.apply_results_filter)
        self.export_button.clicked.connect(self.export_to_csv)
        self.input_title.returnPressed.connect(self.search_jobs)
        self.input_location.returnPressed.connect(self.search_jobs)
        self.input_field.returnPressed.connect(self.search_jobs)

    def search_jobs(self):
        # Make sure location is provided
        if not self.input_location.text().strip():
            QtWidgets.QMessageBox.warning(self, "Fehler", "Bitte gib mindestens einen Ort an.")
            return

        # Clear previous search results
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        self.search_results = []

        # Prepare API request
        url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
        headers = {"X-API-Key": "jobboerse-jobsuche"}
        params = {
            "wo": self.input_location.text().strip(),
            "was": self.input_title.text().strip(),
            "berufsfeld": self.input_field.text().strip(),
            "angebotsart": self.offer_type_input.currentData(),
            "size": 250,
        }
        params = {k: v for k, v in params.items() if v}  # Remove empty parameters

        # Call the API and handle errors
        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            jobs = res.json().get("stellenangebote", [])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"API error:\n{e}")
            return

        # Fill the results table with job offers
        for row, job in enumerate(jobs):
            self.search_results.append(job)
            title = str(job.get("titel", "N/A"))
            company = str(job.get("arbeitgeber", "N/A"))
            loc = job.get("arbeitsort", {})
            location = f"{loc.get('region', '')}, {loc.get('ort', '')}".strip(", ")
            refnr = job.get("refnr", "N/A")
            link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(title))

            # Details button
            detail_btn = QtWidgets.QPushButton("Details")
            detail_btn.clicked.connect(lambda _, r=row: self.toggle_detail_panel_from_search(r))
            self.results_table.setCellWidget(row, 1, detail_btn)
            self.results_table.setItem(row, 2, QtWidgets.QTableWidgetItem(location))
            self.results_table.setItem(row, 3, QtWidgets.QTableWidgetItem(refnr))

            link_button = QtWidgets.QPushButton("Zur Anzeige")
            link_button.clicked.connect(lambda _, url=link: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
            self.results_table.setCellWidget(row, 4, link_button)

            save_button = QtWidgets.QPushButton("Speichern")
            save_button.clicked.connect(lambda _, r=row: self.save_job(r))
            self.results_table.setCellWidget(row, 5, save_button)

        # Finish table setup
        self.results_table.resizeColumnsToContents()
        self.results_table.setSortingEnabled(True)
        self.results_table.resizeRowsToContents()

    def toggle_detail_panel_from_search(self, row):
        if self.detail_box.isVisible() and self.active_saved_row is None and getattr(self, "active_search_row",
                                                                                     None) == row:
            self.close_detail_panel()
            self.update_detail_button_text(row, "Details")
            self.active_search_row = None
            return

        # Save currently open row to toggle
        self.active_search_row = row

        job = self.search_results[row]
        self.label_title.setText(job.get("titel", ""))
        self.label_company.setText(job.get("arbeitgeber", ""))
        loc = job.get("arbeitsort", {})
        self.label_location.setText(f"{loc.get('region', '')}, {loc.get('ort', '')}".strip(", "))
        refnr = job.get("refnr", "N/A")
        self.label_refnr.setText(refnr)
        self.current_link = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

        self.status_input.setCurrentIndex(0)
        self.note_input.clear()
        self.active_saved_row = None

        self.files_label.hide()
        self.file_list_widget.hide()
        self.files_btn_widget.hide()
        self.file_list_widget.setEnabled(False)
        self.add_file_btn.setEnabled(False)
        self.open_file_btn.setEnabled(False)
        self.remove_file_btn.setEnabled(False)

        self.detail_box.setVisible(True)
        self.update_detail_button_text(row, "Details schließen")

    def update_detail_button_text(self, row, text):
        btn = self.results_table.cellWidget(row, 1)
        if isinstance(btn, QtWidgets.QPushButton):
            btn.setText(text)

    def save_job(self, row=None):
        # If editing an existing saved job, update it
        if self.active_saved_row is not None and row is None:
            self.saved_jobs[self.active_saved_row]["status"] = self.status_input.currentText()
            self.saved_jobs[self.active_saved_row]["notes"] = self.note_input.toPlainText()
            save_jobs(self.saved_jobs)
            self.refresh_saved_table()
            self.active_saved_row = None
            self.detail_box.setVisible(False)
            return

        # Otherwise, save a new job from search results
        if row is None or row >= len(self.search_results):
            return
        job = self.search_results[row]
        loc = job.get("arbeitsort", {})
        entry = {
            "title": job.get("titel", ""),
            "company": job.get("arbeitgeber", ""),
            "location": f"{loc.get('region', '')}, {loc.get('ort', '')}".strip(", "),
            "status": self.status_input.currentText(),
            "notes": self.note_input.toPlainText(),
            "refnr": job.get("refnr", "N/A"),
            "link": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{job.get('refnr', '')}",
            "files": []
        }

        if not entry["title"] or not entry["company"]:
            QtWidgets.QMessageBox.warning(self, "Ungültiger Eintrag", "Titel und Firma dürfen nicht leer sein.")
            return

        # Do not save duplicates (same refnr or title/company)
        if any(saved.get("refnr") == entry["refnr"] and saved.get("refnr") != "N/A" for saved in self.saved_jobs) or \
           any(saved["title"] == entry["title"] and saved["company"] == entry["company"] for saved in self.saved_jobs):
            QtWidgets.QMessageBox.warning(self, "Schon gespeichert", "Dieser Job wurde bereits gespeichert.")
            return

        # Add to saved jobs list and table
        self.saved_jobs.append(entry)
        self.add_saved_row(entry)
        save_jobs(self.saved_jobs)

    def toggle_saved_detail_panel(self, row):
        if self.detail_box.isVisible() and self.active_saved_row == row:
            self.close_detail_panel()
            return

        if row >= len(self.saved_jobs):  # Prevent index errors
            return

        job = self.saved_jobs[row]
        self.label_title.setText(job.get("title", ""))
        self.label_company.setText(job.get("company", ""))
        self.label_location.setText(job.get("location", ""))
        self.label_refnr.setText(job.get("refnr", "N/A"))
        self.current_link = job.get("link", "")
        self.status_input.setCurrentText(job.get("status", "New"))
        self.note_input.setText(job.get("notes", ""))

        self.file_list_widget.clear()
        self.file_list_widget.addItems(job.get("files", []))
        self.file_list_widget.setEnabled(True)
        self.files_label.show()
        self.file_list_widget.show()
        self.files_btn_widget.show()
        self.add_file_btn.setEnabled(True)
        self.open_file_btn.setEnabled(True)
        self.remove_file_btn.setEnabled(True)

        self.active_saved_row = row
        self.detail_box.setVisible(True)

    def add_saved_row(self, job):
        if not is_valid_job(job):
            return

        row = self.saved_table.rowCount()
        self.saved_table.insertRow(row)

        # Title
        self.saved_table.setItem(row, 0, QtWidgets.QTableWidgetItem(job.get("title", "")))

        # Details button
        details_btn = QtWidgets.QPushButton("Details")
        details_btn.clicked.connect(lambda _, r=row: self.toggle_saved_detail_panel(r))
        self.saved_table.setCellWidget(row, 1, details_btn)

        # Company
        self.saved_table.setItem(row, 2, QtWidgets.QTableWidgetItem(job.get("company", "")))

        # Location
        self.saved_table.setItem(row, 3, QtWidgets.QTableWidgetItem(job.get("location", "")))

        # Status
        combo = QtWidgets.QComboBox()
        combo.addItems(["New", "Interested", "Applied", "Interview", "Rejected", "Accepted"])
        combo.setCurrentText(job.get("status", "New"))
        combo.setProperty("job_ref", job.get("refnr", ""))
        combo.currentIndexChanged.connect(self.update_saved_status)
        self.saved_table.setCellWidget(row, 4, combo)

        # Notes
        note_item = QtWidgets.QTableWidgetItem(job.get("notes", ""))
        note_item.setFlags(note_item.flags() | QtCore.Qt.ItemIsEditable)
        self.saved_table.setItem(row, 5, note_item)

        # RefNr
        self.saved_table.setItem(row, 6, QtWidgets.QTableWidgetItem(job.get("refnr", "N/A")))

        # Link button
        link_btn = QtWidgets.QPushButton("Zur Anzeige")
        if job.get("link"):
            link_btn.clicked.connect(lambda _, url=job["link"]: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
        self.saved_table.setCellWidget(row, 7, link_btn)

        # Manage files
        manage_btn = QtWidgets.QPushButton("Dateien verwalten")
        manage_btn.clicked.connect(lambda _, ref=job.get("refnr", ""): self.manage_files_dialog_by_ref(ref))
        self.saved_table.setCellWidget(row, 8, manage_btn)

        # Delete
        delete_btn = QtWidgets.QPushButton("Löschen")
        delete_btn.clicked.connect(lambda _, ref=job.get("refnr", ""): self.delete_saved_job_by_ref(ref))
        self.saved_table.setCellWidget(row, 9, delete_btn)

        self.saved_table.resizeColumnsToContents()
        self.saved_table.resizeRowsToContents()


    def manage_files_dialog_by_ref(self, ref):
        # Find job index by its reference and open file dialog
        idx = None
        for i, j in enumerate(self.saved_jobs):
            if str(j.get("refnr", "")) == str(ref):
                idx = i
                break
        if idx is None:
            return
        self.manage_files_dialog(idx)

    def manage_files_dialog(self, row):
        # Dialog for adding, opening, and removing files for a saved job
        if row >= len(self.saved_jobs):
            return
        job = self.saved_jobs[row]
        files = job.setdefault("files", [])

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Dateien verwalten")
        layout = QtWidgets.QVBoxLayout(dialog)

        file_list = QtWidgets.QListWidget()
        file_list.addItems(files)
        layout.addWidget(file_list)

        button_layout = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Hinzufügen")
        open_btn = QtWidgets.QPushButton("Öffnen")
        remove_btn = QtWidgets.QPushButton("Entfernen")
        close_btn = QtWidgets.QPushButton("Fertig")
        button_layout.addWidget(add_btn)
        button_layout.addWidget(open_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        def add_files():
            new_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(dialog, "Dateien auswählen")
            for path in new_paths:
                if path and path not in files:
                    files.append(path)
                    file_list.addItem(path)

        def open_file():
            selected = file_list.currentItem()
            if selected:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(selected.text()))

        def remove_file():
            selected_items = file_list.selectedItems()
            for sel in selected_items:
                files.remove(sel.text())
                file_list.takeItem(file_list.row(sel))

        add_btn.clicked.connect(add_files)
        open_btn.clicked.connect(open_file)
        remove_btn.clicked.connect(remove_file)
        close_btn.clicked.connect(lambda: (save_jobs(self.saved_jobs), dialog.accept()))

        dialog.exec_()
        # Refresh file list if this job is currently open
        if self.active_saved_row is not None and row == self.active_saved_row:
            self.file_list_widget.clear()
            for f in files:
                self.file_list_widget.addItem(f)

    def delete_saved_job_by_ref(self, ref):
        # Remove a job by its reference number
        idx = None
        for i, j in enumerate(self.saved_jobs):
            if str(j.get("refnr", "")) == str(ref):
                idx = i
                break
        if idx is None:
            return

        # Remove from data and file
        del self.saved_jobs[idx]
        save_jobs(self.saved_jobs)

        # Remove from table view
        for r in range(self.saved_table.rowCount()):
            item = self.saved_table.item(r, 6)
            if item and item.text() == str(ref):
                self.saved_table.removeRow(r)
                break

    def update_saved_status(self):
        # Update job status when a combobox changes
        combo = self.sender()
        if not combo:
            return
        ref = combo.property("job_ref")
        new_status = combo.currentText()

        # Update the saved job data
        for job in self.saved_jobs:
            if str(job.get("refnr", "")) == str(ref):
                job["status"] = new_status
                break
        save_jobs(self.saved_jobs)

        # Update the status text in the table for sorting purposes
        for r in range(self.saved_table.rowCount()):
            cell_widget = self.saved_table.cellWidget(r, 3)
            if cell_widget is combo:
                item = self.saved_table.item(r, 3)
                if item:
                    item.setText(new_status)
                break

    def update_saved_note(self, item):
        # Save updated notes when edited in the table
        if item.column() == 4:
            ref_item = self.saved_table.item(item.row(), 5)
            if not ref_item:
                return
            ref = ref_item.text()
            for job in self.saved_jobs:
                if str(job.get("refnr", "")) == str(ref):
                    job["notes"] = item.text()
                    break
            save_jobs(self.saved_jobs)

    def open_job_link(self):
        # Open current job link in browser
        if self.current_link:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.current_link))


    def load_saved_table(self):
        self.saved_jobs = [job for job in load_jobs() if is_valid_job(job)]
        self.saved_table.setSortingEnabled(False)
        for job in self.saved_jobs:
            self.add_saved_row(job)
        self.saved_table.setSortingEnabled(True)
        self.saved_table.resizeColumnsToContents()


    def refresh_saved_table(self):
        # Refresh the saved jobs table after any changes
        self.saved_table.setSortingEnabled(False)
        self.saved_table.setRowCount(0)
        for job in self.saved_jobs:
            self.add_saved_row(job)
        self.saved_table.setSortingEnabled(True)
        self.apply_saved_filter()
        self.saved_table.resizeColumnsToContents()

    def export_to_csv(self):
        # Export saved jobs to CSV file
        if not self.saved_jobs:
            QtWidgets.QMessageBox.information(
                self, "Keine Daten", "Es gibt keine gespeicherten Jobs zum Exportieren."
            )
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "CSV speichern", "saved_jobs.csv", "CSV-Dateien (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "title", "company", "location", "status", "notes", "refnr", "link", "files"
                ])
                writer.writeheader()
                for job in self.saved_jobs:
                    row = job.copy()
                    row["files"] = "; ".join(job.get("files", []))
                    writer.writerow(row)
            QtWidgets.QMessageBox.information(self, "Erfolg", f"Datei wurde gespeichert:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")

    def add_file_to_current_job(self, filepath):
        # Add a file to the current job's file list
        if self.active_saved_row is None:
            QtWidgets.QMessageBox.warning(
                self, "Nicht gespeichert", "Bitte speichere den Job, bevor Dateien hinzugefügt werden."
            )
            return
        job = self.saved_jobs[self.active_saved_row]
        files = job.setdefault("files", [])
        if filepath and filepath not in files:
            files.append(filepath)
            self.file_list_widget.addItem(filepath)
            save_jobs(self.saved_jobs)

    def add_files_dialog(self):
        # Open file dialog to add files to current job
        if self.active_saved_row is None:
            QtWidgets.QMessageBox.warning(
                self, "Nicht gespeichert", "Du musst den Job zuerst speichern, um Dateien hinzuzufügen."
            )
            return
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Dateien auswählen")
        for path in paths:
            if path:
                self.add_file_to_current_job(path)

    def open_selected_file(self):
        # Open selected file(s) from the file list
        items = self.file_list_widget.selectedItems()
        for item in items:
            file_path = item.text()
            if file_path:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

    def remove_selected_files(self):
        # Remove selected files from the current job
        if self.active_saved_row is None:
            return
        items = self.file_list_widget.selectedItems()
        if not items:
            return
        job = self.saved_jobs[self.active_saved_row]
        files = job.setdefault("files", [])
        for it in items:
            file_path = it.text()
            if file_path in files:
                files.remove(file_path)
            self.file_list_widget.takeItem(self.file_list_widget.row(it))
        save_jobs(self.saved_jobs)

    def close_detail_panel(self):
        self.detail_box.setVisible(False)
        self.results_table.clearSelection()
        self.saved_table.clearSelection()
        self.active_saved_row = None

        if hasattr(self, "active_search_row"):
            self.update_detail_button_text(self.active_search_row, "Details")
            self.active_search_row = None

    def apply_saved_filter(self):
        # Filter saved jobs table based on text input
        text = self.saved_filter.text().strip().lower()
        for r in range(self.saved_table.rowCount()):
            row_visible = True
            if text:
                row_visible = False
                for c in [0, 1, 2, 3, 4, 5]:
                    item = self.saved_table.item(r, c)
                    if item and text in item.text().lower():
                        row_visible = True
                        break
            self.saved_table.setRowHidden(r, not row_visible)

    def apply_results_filter(self):
        # Filter search results table based on text input
        text = self.results_filter.text().strip().lower()
        for r in range(self.results_table.rowCount()):
            row_visible = True
            if text:
                row_visible = False
                for c in [0, 1, 2, 3]:
                    item = self.results_table.item(r, c)
                    if item and text in item.text().lower():
                        row_visible = True
                        break
            self.results_table.setRowHidden(r, not row_visible)

    def eventFilter(self, source, event):
        # Close detail panel when clicking outside of tables
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self.detail_box.isVisible():
                if source == self.results_table:
                    idx = source.indexAt(event.pos())
                    if not idx.isValid():  # Clicked empty area
                        self.close_detail_panel()
                elif source == self.saved_table:
                    idx = source.indexAt(event.pos())
                    if not idx.isValid():  # Clicked empty area
                        self.close_detail_panel()
                elif isinstance(source, QtWidgets.QHeaderView):
                    # Clicked header (sorting) – do nothing
                    pass
                else:
                    # Click outside tables and detail
                    detail_rect = QtCore.QRect(
                        self.detail_box.mapToGlobal(QtCore.QPoint(0, 0)), self.detail_box.size()
                    )
                    if not detail_rect.contains(event.globalPos()):
                        self.close_detail_panel()
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()
