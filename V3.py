import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QListWidget, QLabel,
    QHBoxLayout, QMessageBox, QTabWidget
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
        self.detected_categories = {}

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout()
        central_widget.setLayout(self.layout)

        # Left panel
        self.control_panel = QVBoxLayout()

        self.load_button = QPushButton("Load Flight CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.plot_button = QPushButton("Plot Selected Data")
        self.plot_button.clicked.connect(self.plot_selected)

        self.label = QLabel("Detected Variables:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.control_panel.addWidget(self.load_button)
        self.control_panel.addWidget(self.label)
        self.control_panel.addWidget(self.variable_list)
        self.control_panel.addWidget(self.plot_button)

        # Graph area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.layout.addLayout(self.control_panel, 1)
        self.layout.addWidget(self.canvas, 4)

        self.apply_modern_style()

    # ---------- Modern UI ----------
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

    # ---------- Adaptive Column Detection ----------
    def detect_columns(self):
        columns = self.data.columns
        categories = {
            "Time": [],
            "Altitude": [],
            "Velocity": [],
            "Orientation": [],
            "Control": [],
            "Setpoint": [],
            "Apogee": [],
            "Status": [],
            "Other": []
        }

        for col in columns:
            name = col.lower()

            if "time" in name or name == "t":
                categories["Time"].append(col)
                self.time_column = col

            elif "alt" in name or "height" in name:
                categories["Altitude"].append(col)

            elif "vel" in name or "speed" in name:
                categories["Velocity"].append(col)

            elif "yaw" in name or "pitch" in name or "roll" in name:
                categories["Orientation"].append(col)

            elif "servo" in name or "fin" in name:
                categories["Control"].append(col)

            elif "setpoint" in name or "target" in name:
                categories["Setpoint"].append(col)

            elif "apogee" in name:
                categories["Apogee"].append(col)

            elif "status" in name or "mpu" in name or "bmp" in name:
                categories["Status"].append(col)

            else:
                if pd.api.types.is_numeric_dtype(self.data[col]):
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

                # Populate selectable variables (exclude time)
                for category, cols in self.detected_categories.items():
                    for col in cols:
                        if col != self.time_column:
                            self.variable_list.addItem(f"[{category}] {col}")

                QMessageBox.information(self, "Success", "Adaptive Detection Complete!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    # ---------- Plot Selected ----------
    def plot_selected(self):
        if self.data is None:
            QMessageBox.warning(self, "Warning", "Load a CSV file first.")
            return

        selected_items = self.variable_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select at least one variable.")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        time = self.data[self.time_column]

        for item in selected_items:
            text = item.text()
            column = text.split("] ")[1]  # Remove category label
            ax.plot(time, self.data[column], label=column)

        ax.set_xlabel(self.time_column)
        ax.set_title("Adaptive Flight Data Plot")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketDashboard()
    window.show()
    sys.exit(app.exec())