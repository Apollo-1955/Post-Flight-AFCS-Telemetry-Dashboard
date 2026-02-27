import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ================= GRAPH CARD =================
class GraphCard(QGroupBox):

    def __init__(self, title):
        super().__init__(title)

        layout = QVBoxLayout(self)

        self.figure = Figure(facecolor="#151515")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        layout.addWidget(self.canvas)

        self.cursor = None
        self.dot = None
        self.data = None

    def plot(self, time, data, label):

        self.ax.clear()
        self.ax.set_facecolor("#151515")
        self.ax.set_title(label, color="white")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        self.data = data

        self.ax.plot(time, data)

        self.cursor = self.ax.axvline(time[0], linestyle="--")
        self.dot, = self.ax.plot([time[0]], [data[0]], marker="o")

        self.canvas.draw()

    def update_cursor(self, t, index):
        if self.data is None:
            return

        self.cursor.set_xdata([t, t])
        self.dot.set_data([t], [self.data[index]])
        self.canvas.draw_idle()


# ================= GPS MAP =================
class GPSMap(QGroupBox):

    def __init__(self):
        super().__init__("GPS Trajectory")

        layout = QVBoxLayout(self)

        self.figure = Figure(facecolor="#151515")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")

        layout.addWidget(self.canvas)

        self.cursor = None

    def plot(self, lat, lon):

        self.ax.clear()
        self.ax.set_title("Flight Ground Track", color="white")
        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")

        self.ax.plot(lon, lat)

        self.cursor, = self.ax.plot([lon[0]], [lat[0]], marker="o")

        self.lat = lat
        self.lon = lon

        self.canvas.draw()

    def update_cursor(self, index):
        self.cursor.set_data(
            [self.lon[index]],
            [self.lat[index]]
        )
        self.canvas.draw_idle()


# ================= MAIN DASHBOARD =================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Flight Dashboard")
        self.resize(1500, 950)

        self.data = None
        self.time_col = None

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # Controls
        controls = QHBoxLayout()

        self.load_btn = QPushButton("Load CSV")
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")

        controls.addWidget(self.load_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)

        layout.addLayout(controls)

        # Scroll Dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.dashboard = QVBoxLayout(self.container)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        # Timeline slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.slider)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

        self.load_btn.clicked.connect(self.load_csv)
        self.play_btn.clicked.connect(lambda: self.timer.start(20))
        self.pause_btn.clicked.connect(self.timer.stop)
        self.slider.valueChanged.connect(self.update_all)

        self.cards = []
        self.gps_map = None

        self.apply_dark()

    # ---------- Dark UI ----------
    def apply_dark(self):
        self.setStyleSheet("""
            QWidget{background:#121212;color:white;}
            QPushButton{
                background:#1f1f1f;
                padding:6px;
                border-radius:6px;
            }
            QGroupBox{
                border:1px solid #333;
                margin-top:8px;
                font-weight:bold;
            }
        """)

    # ---------- Load CSV ----------
    def load_csv(self):

        path,_ = QFileDialog.getOpenFileName(
            self,"Open CSV","","CSV (*.csv)"
        )
        if not path:
            return

        self.data = pd.read_csv(path)

        for c in self.data.columns:
            if "time" in c.lower():
                self.time_col = c

        time = self.data[self.time_col].values

        # Clear old widgets
        for c in self.cards:
            c.setParent(None)

        self.cards.clear()

        numeric = self.data.select_dtypes(include='number')

        # ---- Flight Section ----
        flight = QLabel("FLIGHT DATA")
        self.dashboard.addWidget(flight)

        for col in numeric.columns:
            if col == self.time_col:
                continue

            card = GraphCard(col)
            card.plot(time, numeric[col].values, col)
            self.dashboard.addWidget(card)

            self.cards.append(card)

        # ---- GPS Detection ----
        lat = None
        lon = None

        for c in self.data.columns:
            name = c.lower()
            if "lat" in name:
                lat = self.data[c].values
            if "lon" in name:
                lon = self.data[c].values

        if lat is not None and lon is not None:
            self.gps_map = GPSMap()
            self.gps_map.plot(lat, lon)
            self.dashboard.addWidget(self.gps_map)

        self.slider.setMaximum(len(time)-1)

    # ---------- Update Cursor ----------
    def update_all(self, index):

        if self.data is None:
            return

        t = self.data[self.time_col].values[index]

        for c in self.cards:
            c.update_cursor(t, index)

        if self.gps_map:
            self.gps_map.update_cursor(index)

    # ---------- Playback ----------
    def animate(self):
        v = self.slider.value()+1
        if v >= self.slider.maximum():
            self.timer.stop()
            return
        self.slider.setValue(v)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RocketDashboard()
    win.show()
    sys.exit(app.exec())