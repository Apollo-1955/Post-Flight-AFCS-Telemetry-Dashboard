import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# =====================================================
# GRAPH CARD (SIDE LABEL STYLE)
# =====================================================
class GraphCard(QWidget):

    def __init__(self, title):
        super().__init__()

        layout = QHBoxLayout(self)

        # ---------- SIDE LABEL ----------
        label_layout = QVBoxLayout()

        self.label = QLabel(title)
        self.label.setFixedWidth(150)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignTop |
            Qt.AlignmentFlag.AlignHCenter
        )

        self.label.setStyleSheet("""
            font-size:14px;
            font-weight:bold;
        """)

        label_layout.addWidget(self.label)
        label_layout.addStretch()

        layout.addLayout(label_layout)

        # ---------- GRAPH ----------
        self.figure = Figure(facecolor="#151515")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        layout.addWidget(self.canvas, 1)

        self.data = None
        self.cursor = None
        self.dot = None

    # ================= Plot =================
    def plot(self, time, data):

        self.ax.clear()
        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        self.data = data
        self.time = time

        self.ax.plot(time, data)

        self.cursor = self.ax.axvline(time[0], linestyle="--")
        self.dot, = self.ax.plot(
            [time[0]],
            [data[0]],
            marker="o"
        )

        self.canvas.draw()

    # ================= Flight Phases =================
    def draw_phases(self, phases):

        colors = {
            "Boost": "orange",
            "Coast": "cyan",
            "Apogee": "yellow",
            "Descent": "red",
            "Landed": "lime"
        }

        for name, t in phases.items():
            self.ax.axvline(
                t,
                linestyle=":",
                color=colors.get(name, "white"),
                alpha=0.8
            )

            self.ax.text(
                t,
                self.ax.get_ylim()[1],
                name,
                rotation=90,
                color=colors.get(name),
                verticalalignment="top"
            )

        self.canvas.draw()

    # ================= Cursor =================
    def update_cursor(self, t, index):

        if self.data is None:
            return

        self.cursor.set_xdata([t, t])
        self.dot.set_data([t], [self.data[index]])

        self.canvas.draw_idle()


# =====================================================
# GPS MAP
# =====================================================
class GPSMap(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        label = QLabel("GPS Path")
        label.setFixedWidth(150)
        layout.addWidget(label)

        self.figure = Figure(facecolor="#151515")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")

        layout.addWidget(self.canvas)

    def plot(self, lat, lon):

        self.lat = lat
        self.lon = lon

        self.ax.clear()
        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#333")

        self.ax.plot(lon, lat)
        self.cursor, = self.ax.plot(
            [lon[0]],
            [lat[0]],
            marker="o"
        )

        self.canvas.draw()

    def update_cursor(self, index):

        self.cursor.set_data(
            [self.lon[index]],
            [self.lat[index]]
        )
        self.canvas.draw_idle()


# =====================================================
# MAIN DASHBOARD
# =====================================================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Flight Analysis")
        self.resize(1500, 950)

        self.data = None
        self.cards = []

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # ---------- Controls ----------
        controls = QHBoxLayout()

        self.load_btn = QPushButton("Load CSV")
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")

        controls.addWidget(self.load_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)

        layout.addLayout(controls)

        # ---------- Scroll Area ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.dashboard = QVBoxLayout(self.container)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        # ---------- Slider ----------
        self.slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.slider)

        # ---------- Timer ----------
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

        self.load_btn.clicked.connect(self.load_csv)
        self.play_btn.clicked.connect(lambda: self.timer.start(20))
        self.pause_btn.clicked.connect(self.timer.stop)
        self.slider.valueChanged.connect(self.update_all)

        self.apply_dark()

    # =====================================================
    # DARK MODE
    # =====================================================
    def apply_dark(self):
        self.setStyleSheet("""
            QWidget{background:#121212;color:white;}
            QPushButton{
                background:#1f1f1f;
                padding:6px;
                border-radius:6px;
            }
        """)

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    def detect(self, keywords):
        for c in self.data.columns:
            name = c.lower()
            for k in keywords:
                if k in name:
                    return c
        return None

    # =====================================================
    # FLIGHT PHASE DETECTION
    # =====================================================
    def detect_phases(self, time, altitude):

        vel = np.gradient(altitude, time)

        boost = np.argmax(vel > 5)
        apogee = np.argmax(altitude)
        descent = apogee + np.argmax(vel[apogee:] < -2)

        landed = len(altitude) - np.argmax(
            altitude[::-1] > altitude.min() + 2
        )

        return {
            "Boost": time[boost],
            "Coast": time[int((boost + apogee)/2)],
            "Apogee": time[apogee],
            "Descent": time[descent],
            "Landed": time[landed-1]
        }

    # =====================================================
    # LOAD CSV
    # =====================================================
    def load_csv(self):

        path,_ = QFileDialog.getOpenFileName(
            self,"Open CSV","","CSV (*.csv)"
        )
        if not path:
            return

        self.data = pd.read_csv(path)

        time_col = self.detect(["time"])
        alt_col = self.detect(["alt"])

        time = self.data[time_col].values
        altitude = self.data[alt_col].values

        phases = self.detect_phases(time, altitude)

        numeric = self.data.select_dtypes(include='number')

        # Clear old
        for c in self.cards:
            c.setParent(None)
        self.cards.clear()

        title = QLabel("FLIGHT DATA")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        self.dashboard.addWidget(title)

        for col in numeric.columns:
            if col == time_col:
                continue

            card = GraphCard(col)
            card.plot(time, numeric[col].values)
            card.draw_phases(phases)

            self.dashboard.addWidget(card)
            self.cards.append(card)

        # GPS
        lat = self.detect(["lat"])
        lon = self.detect(["lon"])

        if lat and lon:
            self.gps = GPSMap()
            self.gps.plot(
                self.data[lat].values,
                self.data[lon].values
            )
            self.dashboard.addWidget(self.gps)

        self.time = time
        self.slider.setMaximum(len(time)-1)

    # =====================================================
    # UPDATE CURSOR
    # =====================================================
    def update_all(self, index):

        t = self.time[index]

        for c in self.cards:
            c.update_cursor(t, index)

        if hasattr(self, "gps"):
            self.gps.update_cursor(index)

    # =====================================================
    # PLAYBACK
    # =====================================================
    def animate(self):

        v = self.slider.value()+1
        if v >= self.slider.maximum():
            self.timer.stop()
            return

        self.slider.setValue(v)


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = RocketDashboard()
    win.show()

    sys.exit(app.exec())