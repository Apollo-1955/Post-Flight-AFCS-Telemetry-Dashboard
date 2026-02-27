import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog,
    QLabel, QSlider
)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# =============================
# DARK MODE
# =============================
def enable_dark(app):
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)

    app.setPalette(palette)


# =============================
# GRAPH WIDGET
# =============================
class GraphCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(facecolor="#1e1e1e")
        super().__init__(self.fig)


# =============================
# MAIN WINDOW
# =============================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rocket Post-Flight Analysis")
        self.resize(1500, 900)

        self.data = None
        self.time_index = 0

        main = QWidget()
        self.setCentralWidget(main)

        layout = QHBoxLayout(main)

        # =============================
        # SIDE CONTROL PANEL
        # =============================
        side = QVBoxLayout()

        self.open_btn = QPushButton("Open CSV")
        self.open_btn.clicked.connect(self.load_csv)

        self.play_btn = QPushButton("▶ Playback")
        self.play_btn.clicked.connect(self.toggle_playback)

        self.info_label = QLabel("No Data Loaded")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.update_cursor)

        side.addWidget(self.open_btn)
        side.addWidget(self.play_btn)
        side.addWidget(QLabel("Timeline"))
        side.addWidget(self.slider)
        side.addWidget(self.info_label)
        side.addStretch()

        layout.addLayout(side, 1)

        # =============================
        # GRAPH AREA
        # =============================
        graphs = QVBoxLayout()

        self.alt_graph = GraphCanvas()
        self.vel_graph = GraphCanvas()
        self.acc_graph = GraphCanvas()
        self.gps_graph = GraphCanvas()

        graphs.addWidget(self.alt_graph)
        graphs.addWidget(self.vel_graph)
        graphs.addWidget(self.acc_graph)
        graphs.addWidget(self.gps_graph)

        layout.addLayout(graphs, 4)

        # playback timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

    # =============================
    # COLUMN DETECTION
    # =============================
    def detect(self, keywords):
        for col in self.data.columns:
            name = col.lower()
            for k in keywords:
                if k in name:
                    return col
        return None

    # =============================
    # LOAD CSV
    # =============================
    def load_csv(self):

        file, _ = QFileDialog.getOpenFileName(
            self, "Open Flight Data", "", "CSV Files (*.csv)"
        )

        if not file:
            return

        self.data = pd.read_csv(file)

        self.time_col = self.detect(["time"])
        self.alt_col = self.detect(["alt"])
        self.vel_col = self.detect(["vel"])
        self.ax = self.detect(["accelx", "ax"])
        self.ay = self.detect(["accely", "ay"])
        self.az = self.detect(["accelz", "az"])
        self.lat = self.detect(["lat"])
        self.lon = self.detect(["lon"])

        self.slider.setMaximum(len(self.data) - 1)

        self.plot_all()

    # =============================
    # MAIN PLOTTING
    # =============================
    def plot_all(self):

        t = self.data[self.time_col]

        # ---------- ALTITUDE ----------
        ax = self.alt_graph.fig.subplots()
        ax.clear()

        alt = self.data[self.alt_col]

        ax.plot(t, alt)

        apogee_index = alt.idxmax()
        apogee_time = t[apogee_index]
        apogee_alt = alt[apogee_index]

        ax.axvline(apogee_time, linestyle="--")
        ax.scatter(apogee_time, apogee_alt)

        ax.set_title("Altitude vs Time")
        self.alt_graph.draw()

        # ---------- VELOCITY ----------
        ax2 = self.vel_graph.fig.subplots()
        ax2.clear()

        if self.vel_col:
            ax2.plot(t, self.data[self.vel_col])

        ax2.set_title("Velocity vs Time")
        self.vel_graph.draw()

        # ---------- ACCEL ----------
        ax3 = self.acc_graph.fig.subplots()
        ax3.clear()

        if self.ax:
            ax3.plot(t, self.data[self.ax], label="X")
        if self.ay:
            ax3.plot(t, self.data[self.ay], label="Y")
        if self.az:
            ax3.plot(t, self.data[self.az], label="Z")

        ax3.legend()
        ax3.set_title("Acceleration XYZ")
        self.acc_graph.draw()

        # ---------- GPS ----------
        ax4 = self.gps_graph.fig.subplots()
        ax4.clear()

        if self.lat and self.lon:
            ax4.plot(
                self.data[self.lon],
                self.data[self.lat]
            )
            ax4.set_xlabel("Longitude")
            ax4.set_ylabel("Latitude")

        ax4.set_title("GPS Flight Path")
        self.gps_graph.draw()

    # =============================
    # CURSOR + DOT FOLLOW
    # =============================
    def update_cursor(self, value):

        if self.data is None:
            return

        time_val = self.data[self.time_col][value]
        alt_val = self.data[self.alt_col][value]

        self.info_label.setText(
            f"Time: {time_val:.2f}s\nAltitude: {alt_val:.2f}m"
        )

        ax = self.alt_graph.fig.axes[0]
        ax.lines = ax.lines[:1]

        ax.axvline(time_val)

        ax.scatter(time_val, alt_val)

        self.alt_graph.draw()

    # =============================
    # PLAYBACK
    # =============================
    def toggle_playback(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(40)

    def animate(self):
        v = self.slider.value()
        if v < self.slider.maximum():
            self.slider.setValue(v + 1)
        else:
            self.timer.stop()


# =============================
# RUN
# =============================
app = QApplication(sys.argv)
enable_dark(app)

window = RocketDashboard()
window.show()

sys.exit(app.exec())