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

        self.setWindowTitle("🚀 Rocket Flight Analysis Dashboard")
        self.setGeometry(200, 100, 1500, 900)

        self.data = None
        self.time_column = None
        self.altitude_column = None
        self.current_ax = None
        self.cursor_line = None
        self.selected_columns = []

        # =============================
        # MAIN LAYOUT
        # =============================
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)

        # =============================
        # CONTROL PANEL
        # =============================
        control_layout = QVBoxLayout()

        self.load_button = QPushButton("Load Flight CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.plot_button = QPushButton("Plot Selected Data")
        self.plot_button.clicked.connect(self.plot_selected)

        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )

        self.telemetry_label = QLabel("Telemetry:")
        self.telemetry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.telemetry_label.setStyleSheet(
            "font-weight:bold;font-size:15px;"
        )

        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.variable_list)
        control_layout.addWidget(self.plot_button)
        control_layout.addStretch()
        control_layout.addWidget(self.telemetry_label)

        # =============================
        # GRAPH AREA
        # =============================
        graph_layout = QVBoxLayout()

        self.figure = Figure(
            facecolor="#121212",
            constrained_layout=True   # ⭐ FIX CLIPPING
        )

        self.canvas = FigureCanvas(self.figure)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.slider_moved)

        graph_layout.addWidget(self.canvas)
        graph_layout.addWidget(self.slider)

        self.main_layout.addLayout(control_layout, 1)
        self.main_layout.addLayout(graph_layout, 4)

        self.apply_dark_theme()

    # =============================
    # DARK UI
    # =============================
    def apply_dark_theme(self):
        self.setStyleSheet("""
        QWidget {
            background:#121212;
            color:#E0E0E0;
            font-size:14px;
        }

        QPushButton {
            background:#1F1F1F;
            border:1px solid #333;
            padding:8px;
            border-radius:6px;
        }

        QPushButton:hover {
            background:#2A2A2A;
        }

        QListWidget {
            background:#1A1A1A;
            border:1px solid #333;
        }
        """)

    # =============================
    # COLUMN DETECTION
    # =============================
    def detect_columns(self):
        self.time_column = None
        self.altitude_column = None

        for col in self.data.columns:
            name = col.lower()

            if "time" in name:
                self.time_column = col

            if "alt" in name or "height" in name:
                self.altitude_column = col

    # =============================
    # LOAD CSV
    # =============================
    def load_csv(self):

        file, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV Files (*.csv)"
        )

        if not file:
            return

        try:
            self.data = pd.read_csv(file)
            self.variable_list.clear()

            self.detect_columns()

            if not self.time_column:
                raise Exception("No time column detected")

            numeric = self.data.select_dtypes(
                include="number"
            ).columns

            for col in numeric:
                if col != self.time_column:
                    self.variable_list.addItem(col)

            QMessageBox.information(self, "Success", "CSV Loaded!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # =============================
    # GRAPH STYLE
    # =============================
    def style_axis(self, ax):

        ax.set_facecolor("#121212")

        for spine in ax.spines.values():
            spine.set_color("white")

        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")

        ax.grid(True, color="#333")

    # =============================
    # PLOT
    # =============================
    def plot_selected(self):

        if self.data is None:
            return

        items = self.variable_list.selectedItems()

        if not items:
            QMessageBox.warning(
                self, "Warning", "Select variables"
            )
            return

        self.selected_columns = [i.text() for i in items]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self.current_ax = ax

        self.style_axis(ax)

        time = self.data[self.time_column].values

        for col in self.selected_columns:
            ax.plot(time, self.data[col], label=col)

        # ===== Apogee =====
        if self.altitude_column:
            altitude = self.data[self.altitude_column]
            idx = np.argmax(altitude)

            ax.scatter(
                time[idx],
                altitude[idx],
                s=100
            )

            ax.annotate(
                f"Apogee\n{altitude[idx]:.2f} m",
                (time[idx], altitude[idx]),
                xytext=(10, 10),
                textcoords="offset points",
                color="white"
            )

        ax.set_xlabel("Time (s)")
        ax.set_title("Flight Data Analysis")

        ax.legend(
            facecolor="#1A1A1A",
            edgecolor="white"
        )

        self.cursor_line = ax.axvline(
            time[0],
            linestyle="--"
        )

        self.canvas.draw_idle()

        # Slider
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(time) - 1)
        self.slider.setValue(0)
        self.slider.setEnabled(True)

    # =============================
    # SLIDER TELEMETRY
    # =============================
    def slider_moved(self, index):

        if self.current_ax is None:
            return

        time = self.data[self.time_column].values
        t = time[index]

        self.cursor_line.set_xdata([t, t])

        text = f"Time: {t:.2f}s"

        for col in self.selected_columns:
            val = self.data[col].values[index]
            text += f" | {col}: {val:.2f}"

        self.telemetry_label.setText("Telemetry: " + text)

        self.canvas.draw_idle()


# =============================
# RUN
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RocketDashboard()
    win.show()
    sys.exit(app.exec())