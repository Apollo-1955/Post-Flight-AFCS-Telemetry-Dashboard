import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MiniGraph:
    """Individual telemetry graph"""

    def __init__(self, parent_layout, title):

        self.figure = Figure(facecolor="#121212")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor("#121212")
        self.ax.set_title(title, color="white")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        parent_layout.addWidget(self.canvas)

        self.line = None
        self.cursor = None
        self.dot = None

    def plot(self, time, data, label):
        self.ax.clear()

        self.ax.set_facecolor("#121212")
        self.ax.set_title(label, color="white")
        self.ax.grid(True, color="#333")
        self.ax.tick_params(colors="white")

        self.line, = self.ax.plot(time, data)

        self.cursor = self.ax.axvline(time[0], linestyle="--")

        self.dot, = self.ax.plot(
            [time[0]],
            [data[0]],
            marker="o"
        )

        self.canvas.draw()

    def update_cursor(self, t, y):
        self.cursor.set_xdata([t, t])
        self.dot.set_data([t], [y])
        self.canvas.draw_idle()


class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Flight Analysis System")
        self.resize(1500, 950)

        self.data = None
        self.time_col = None

        self.graphs = []

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # -------- Buttons --------
        btn_layout = QHBoxLayout()

        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)

        self.play_btn = QPushButton("▶ Play")
        self.pause_btn = QPushButton("⏸ Pause")

        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.pause_btn)

        layout.addLayout(btn_layout)

        # -------- Scroll Graph Area --------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)

        scroll.setWidget(self.graph_container)
        layout.addWidget(scroll)

        # -------- Slider --------
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.slider_update)
        layout.addWidget(self.slider)

        # Playback timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

        self.play_btn.clicked.connect(self.start_playback)
        self.pause_btn.clicked.connect(self.timer.stop)

        self.apply_dark()

    # ---------- Dark Theme ----------
    def apply_dark(self):
        self.setStyleSheet("""
            QWidget {background:#121212;color:white;}
            QPushButton {
                background:#1f1f1f;
                padding:6px;
                border-radius:6px;
            }
        """)

    # ---------- Load CSV ----------
    def load_csv(self):

        path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV (*.csv)"
        )

        if not path:
            return

        self.data = pd.read_csv(path)

        # detect time
        for c in self.data.columns:
            if "time" in c.lower():
                self.time_col = c

        time = self.data[self.time_col].values

        # remove old graphs
        for g in self.graphs:
            g.canvas.setParent(None)

        self.graphs.clear()

        # auto create mini graphs
        numeric = self.data.select_dtypes(include='number')

        for col in numeric.columns:
            if col == self.time_col:
                continue

            graph = MiniGraph(self.graph_layout, col)
            graph.plot(time, numeric[col].values, col)

            self.graphs.append((graph, col))

        self.slider.setMaximum(len(time)-1)

    # ---------- Slider Control ----------
    def slider_update(self, index):

        if self.data is None:
            return

        time = self.data[self.time_col].values
        t = time[index]

        for graph, col in self.graphs:
            y = self.data[col].values[index]
            graph.update_cursor(t, y)

    # ---------- Playback ----------
    def start_playback(self):
        self.timer.start(20)

    def animate(self):
        v = self.slider.value() + 1

        if v >= self.slider.maximum():
            self.timer.stop()
            return

        self.slider.setValue(v)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RocketDashboard()
    win.show()
    sys.exit(app.exec())