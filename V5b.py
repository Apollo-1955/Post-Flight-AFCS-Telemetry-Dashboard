import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QListWidget, QLabel,
    QHBoxLayout, QMessageBox, QSlider
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RocketDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Advanced Rocket Flight Dashboard")
        self.setGeometry(200, 100, 1400, 900)

        self.data = None
        self.time_column = None
        self.altitude_column = None
        self.current_ax = None
        self.cursor_line = None

        # Layout setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout()
        central_widget.setLayout(self.main_layout)

        # Control panel
        self.control_panel = QVBoxLayout()

        self.load_button = QPushButton("Load Flight CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.plot_button = QPushButton("Plot Selected Data")
        self.plot_button.clicked.connect(self.plot_selected)

        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.telemetry_label = QLabel("Telemetry:")
        self.telemetry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.control_panel.addWidget(self.load_button)
        self.control_panel.addWidget(self.variable_list)
        self.control_panel.addWidget(self.plot_button)
        self.control_panel.addWidget(self.telemetry_label)

        # Graph + slider layout
        self.graph_layout = QVBoxLayout()

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.slider_moved)

        self.graph_layout.addWidget(self.canvas)
        self.graph_layout.addWidget(self.slider)

        self.main_layout.addLayout(self.control_panel, 1)
        self.main_layout.addLayout(self.graph_layout, 4)

    # -------- Column Detection --------
    def detect_columns(self):
        self.time_column = None
        self.altitude_column = None

        for col in self.data.columns:
            name = col.lower()
            if "time" in name:
                self.time_column = col
            if "alt" in name or "height" in name:
                self.altitude_column = col

    # -------- Load CSV --------
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Flight CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            self.data = pd.read_csv(file_path)
            self.variable_list.clear()
            self.detect_columns()

            if not self.time_column:
                QMessageBox.critical(self, "Error", "No time column detected!")
                return

            numeric_cols = self.data.select_dtypes(include='number').columns
            for col in numeric_cols:
                if col != self.time_column:
                    self.variable_list.addItem(col)

            QMessageBox.information(self, "Success", "CSV Loaded!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # -------- Plot --------
    def plot_selected(self):
        if self.data is None:
            return

        selected_items = self.variable_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select at least one variable.")
            return

        self.figure.clear()
        self.current_ax = self.figure.add_subplot(111)

        time = self.data[self.time_column].values

        for item in selected_items:
            column = item.text()
            self.current_ax.plot(time, self.data[column].values, label=column)

        # Apogee detection
        if self.altitude_column:
            altitude = self.data[self.altitude_column].values
            apogee_idx = np.argmax(altitude)
            self.current_ax.scatter(time[apogee_idx], altitude[apogee_idx], s=100)
            self.current_ax.annotate(
                f"Apogee\n{altitude[apogee_idx]:.2f} m",
                (time[apogee_idx], altitude[apogee_idx]),
                textcoords="offset points",
                xytext=(10, 10)
            )

        self.current_ax.set_xlabel("Time (s)")
        self.current_ax.set_title("Flight Data Analysis")
        self.current_ax.legend()
        self.current_ax.grid(True)

        # Create tracking line AFTER plot exists
        self.cursor_line = self.current_ax.axvline(time[0], linestyle="--")

        self.canvas.draw()

        # Enable slider
        self.slider.blockSignals(True)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(time) - 1)
        self.slider.setValue(0)
        self.slider.setEnabled(True)
        self.slider.blockSignals(False)

    # -------- Slider Movement --------
    def slider_moved(self, index):
        if self.data is None or self.current_ax is None:
            return

        time = self.data[self.time_column].values
        current_time = time[index]

        # IMPORTANT FIX: must pass a sequence
        self.cursor_line.set_xdata([current_time, current_time])

        telemetry = f"Time: {current_time:.2f}s"

        if self.altitude_column:
            altitude = self.data[self.altitude_column].values[index]
            telemetry += f" | Altitude: {altitude:.2f} m"

        self.telemetry_label.setText("Telemetry: " + telemetry)

        self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketDashboard()
    window.show()
    sys.exit(app.exec())