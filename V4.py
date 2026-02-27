import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QListWidget, QLabel,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RocketDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Adaptive Rocket Flight Dashboard")
        self.setGeometry(200, 100, 1400, 850)

        self.data = None
        self.time_column = None
        self.altitude_column = None
        self.detected_categories = {}

        # ---------- UI Layout ----------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout()
        central_widget.setLayout(self.layout)

        self.control_panel = QVBoxLayout()

        self.load_button = QPushButton("Load Flight CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.plot_button = QPushButton("Plot Selected Data")
        self.plot_button.clicked.connect(self.plot_selected)

        self.label = QLabel("Detected Variables:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.telemetry_label = QLabel("Telemetry: ")
        self.telemetry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.control_panel.addWidget(self.load_button)
        self.control_panel.addWidget(self.label)
        self.control_panel.addWidget(self.variable_list)
        self.control_panel.addWidget(self.plot_button)
        self.control_panel.addWidget(self.telemetry_label)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.layout.addLayout(self.control_panel, 1)
        self.layout.addWidget(self.canvas, 4)

        self.apply_modern_style()

        # Interactive cursor elements
        self.cursor_line = None

    # ---------- Modern Dark UI ----------
    def apply_modern_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3a3f5a;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #50577a;
            }
            QListWidget {
                background-color: #2a2f45;
                border-radius: 6px;
            }
        """)

    # ---------- Column Detection ----------
    def detect_columns(self):
        columns = self.data.columns
        categories = {"Time": [], "Altitude": [], "Other": []}

        for col in columns:
            name = col.lower()

            if "time" in name:
                categories["Time"].append(col)
                self.time_column = col

            elif "alt" in name or "height" in name:
                categories["Altitude"].append(col)
                self.altitude_column = col

            elif pd.api.types.is_numeric_dtype(self.data[col]):
                categories["Other"].append(col)

        self.detected_categories = categories

    # ---------- Load CSV ----------
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Flight CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.variable_list.clear()

                self.detect_columns()

                if not self.time_column:
                    QMessageBox.critical(self, "Error", "No time column detected!")
                    return

                for category, cols in self.detected_categories.items():
                    for col in cols:
                        if col != self.time_column:
                            self.variable_list.addItem(col)

                QMessageBox.information(self, "Success", "CSV Loaded & Analyzed!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    # ---------- Plot Selected ----------
    def plot_selected(self):
        if self.data is None:
            return

        selected_items = self.variable_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select at least one variable.")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        time = self.data[self.time_column]

        for item in selected_items:
            column = item.text()
            ax.plot(time, self.data[column], label=column)

        # ---------- AUTO APOGEE DETECTION ----------
        if self.altitude_column:
            altitude = self.data[self.altitude_column]
            apogee_index = altitude.idxmax()
            apogee_time = time[apogee_index]
            apogee_alt = altitude[apogee_index]

            ax.scatter(apogee_time, apogee_alt, s=100)
            ax.annotate(
                f"Apogee\n{apogee_alt:.2f} m\n@ {apogee_time:.2f} s",
                (apogee_time, apogee_alt),
                textcoords="offset points",
                xytext=(10, 10)
            )

        ax.set_xlabel(self.time_column)
        ax.set_title("Flight Data with Apogee Detection")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()

        # ---------- Interactive Mouse Tracking ----------
        self.cursor_line = ax.axvline(x=0)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

    # ---------- Mouse Hover Telemetry ----------
    def on_mouse_move(self, event):
        if not event.inaxes or self.data is None:
            return

        time = self.data[self.time_column].values
        mouse_time = event.xdata

        idx = (np.abs(time - mouse_time)).argmin()
        nearest_time = time[idx]

        self.cursor_line.set_xdata(nearest_time)

        telemetry_text = f"Time: {nearest_time:.2f}s"

        if self.altitude_column:
            altitude = self.data[self.altitude_column].values[idx]
            telemetry_text += f" | Altitude: {altitude:.2f} m"

        self.telemetry_label.setText("Telemetry: " + telemetry_text)

        self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketDashboard()
    window.show()
    sys.exit(app.exec())