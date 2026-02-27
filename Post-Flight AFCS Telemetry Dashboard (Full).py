import os
import sys
import pandas as pd
import numpy as np
import matplotlib as mpl


from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


# =====================================================
# GLOBAL DARK MATPLOTLIB STYLE
# =====================================================
mpl.rcParams.update({
    "text.color": "white",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "axes.edgecolor": "white"
})

def resource_path(relative_path):
    """Get absolute path to resource (works for exe + python)"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class PopOutWindow(QWidget):
    """Standalone window to host the popped-out graph."""

    def __init__(self, canvas, parent_layout, parent_widget):
        super().__init__()
        self.setWindowTitle("External Telemetry View")
        self.resize(1100, 700)
        self.canvas = canvas
        self.parent_layout = parent_layout
        self.parent_widget = parent_widget

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.canvas)

    def closeEvent(self, event):
        """Safely return the canvas to the main dashboard layout when window closes."""
        self.parent_layout.addWidget(self.canvas)
        super().closeEvent(event)


class HUDGauge(QWidget):
    def __init__(self, title, min_val=0, max_val=100, unit="", color="#4CAF50"):
        super().__init__()
        self.title, self.min_val, self.max_val = title, min_val, max_val
        self.value = min_val
        self.unit = unit
        self.fill_ratio = 0
        self.base_color = QColor(color)
        self.display_color = QColor(color)
        self.setMinimumSize(200, 160)

    def update_limits(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val if max_val != min_val else max_val + 0.001
        self.update()

    def set_value(self, val, velocity_ratio=0):
        self.value = val
        range_size = self.max_val - self.min_val
        self.fill_ratio = np.clip((val - self.min_val) / range_size, 0, 1)

        r = int(self.base_color.red() + (255 - self.base_color.red()) * velocity_ratio)
        g = int(self.base_color.green() * (1 - velocity_ratio))
        self.display_color = QColor(r, g, self.base_color.blue())
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(20, 20, self.width() - 40, self.width() - 40)
        p.setPen(QPen(QColor(40, 40, 40), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, -30 * 16, 240 * 16)
        p.setPen(QPen(self.display_color, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 210 * 16, int(-self.fill_ratio * 240 * 16))
        p.setPen(QColor("white"))
        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        p.drawText(self.rect().adjusted(0, -10, 0, 0), Qt.AlignmentFlag.AlignCenter, f"{self.value:.2f}")
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter, f"{self.title}\n({self.unit})")


class RocketDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Post-Flight Telemetry AFCS Data Dashboard")
        self.setGeometry(100, 100, 1600, 900)

        self.data = None
        self.time_col, self.alt_col, self.vel_col = None, None, None
        self.yaw_col, self.yaw_sp_col, self.servo_col = None, None, None
        self.acc_cols = {"x": None, "y": None, "z": None}

        self.current_ax = None
        self.intersection_dots = {}
        self._bg_cache = None
        self.popout_window = None

        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.step_forward)

        self.init_ui()
        self.apply_dark()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Left Control Side
        control = QVBoxLayout()

        # Buttons Group
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.view_btn = QPushButton("HUD Mode")
        self.view_btn.setCheckable(True)
        self.view_btn.clicked.connect(self.toggle_view)
        self.pop_btn = QPushButton("Pop Out Graph")
        self.pop_btn.clicked.connect(self.pop_out_graph)

        # Variable List
        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.plot_btn = QPushButton("Plot")
        self.plot_btn.clicked.connect(self.plot_selected)

        # Summary Table (Bottom Left)
        self.stats_table = QTableWidget(5, 2)
        self.stats_table.setHorizontalHeaderLabels(["Parameter", "Maximum"])
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stats_table.setFixedHeight(180)
        self.init_stats_table()

        self.telemetry = QLabel("System Ready")
        self.telemetry.setStyleSheet("font-family: Consolas; color: #00FF00; font-size: 13px;")

        control.addWidget(self.load_btn)
        control.addWidget(self.play_btn)
        control.addWidget(self.view_btn)
        control.addWidget(self.pop_btn)
        control.addWidget(QLabel("Telemetry Channels:"))
        control.addWidget(self.variable_list)
        control.addWidget(self.plot_btn)
        control.addWidget(QLabel("Flight Maxima:"))
        control.addWidget(self.stats_table)
        control.addWidget(self.telemetry)

        # Right Content Side
        self.stack = QStackedWidget()
        self.graph_page = QWidget()
        self.gv_layout = QVBoxLayout(self.graph_page)
        self.figure = Figure(facecolor="#121212", constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.gv_layout.addWidget(self.canvas)

        hud_page = QWidget()
        self.hud_grid = QGridLayout(hud_page)
        self.setup_hud_widgets()

        self.stack.addWidget(self.graph_page)
        self.stack.addWidget(hud_page)

        timeline_layout = QVBoxLayout()
        timeline_layout.addWidget(self.stack)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.slider_moved)
        self.slider.setEnabled(False)
        timeline_layout.addWidget(self.slider)

        layout.addLayout(control, 1)
        layout.addLayout(timeline_layout, 5)

    def init_stats_table(self):
        params = ["Altitude", "Velocity", "X Accel", "Y Accel", "Z Accel"]
        for i, name in enumerate(params):
            self.stats_table.setItem(i, 0, QTableWidgetItem(name))
            self.stats_table.setItem(i, 1, QTableWidgetItem("0.00"))

    def setup_hud_widgets(self):
        self.alt_gauge = HUDGauge("Altitude", unit="m", color="#4CAF50")
        self.vel_gauge = HUDGauge("Velocity", unit="m/s", color="#2196F3")
        self.servo_gauge = HUDGauge("Servo Pos", unit="deg", color="#E91E63")
        self.yaw_gauge = HUDGauge("Yaw Actual", unit="deg", color="#00BCD4")
        self.yaw_sp_gauge = HUDGauge("Yaw Setpoint", unit="deg", color="#FF9800")

        self.hud_grid.addWidget(self.alt_gauge, 0, 0)
        self.hud_grid.addWidget(self.vel_gauge, 0, 1)
        self.hud_grid.addWidget(self.servo_gauge, 0, 2)
        self.hud_grid.addWidget(self.yaw_gauge, 1, 0)
        self.hud_grid.addWidget(self.yaw_sp_gauge, 1, 1)

    def apply_dark(self):
        self.setStyleSheet("""
            QWidget { background: #0A0A0A; color: white; }
            QPushButton { background: #1F1F1F; border: 1px solid #333; padding: 10px; border-radius: 4px; }
            QPushButton:checked { background: #153A15; border-color: #4CAF50; }
            QListWidget, QTableWidget { background: #111; border: 1px solid #222; gridline-color: #333; }
            QHeaderView::section { background-color: #222; color: white; border: 1px solid #333; }
            QSlider::handle:horizontal { background: #4CAF50; width: 16px; height: 16px; border-radius: 8px; }
        """)

    def pop_out_graph(self):
        if not self.popout_window or not self.popout_window.isVisible():
            self.popout_window = PopOutWindow(self.canvas, self.gv_layout, self.graph_page)
            self.popout_window.show()

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Flight Logs", "", "CSV (*.csv)")
        if not path: return
        self.data = pd.read_csv(path)
        self.variable_list.clear()

        for c in self.data.columns:
            low = c.lower()
            if "time" in low:
                self.time_col = c
            elif "alt" in low:
                self.alt_col = c
            elif "vel" in low:
                self.vel_col = c
            elif "yaw" in low and ("set" not in low and "sp" not in low):
                self.yaw_col = c
            elif "set" in low or "sp" in low:
                self.yaw_sp_col = c
            elif "servo" in low or "pos" in low:
                self.servo_col = c

            # Acceleration mapping
            if "accel" in low or "acc" in low:
                if "x" in low:
                    self.acc_cols["x"] = c
                elif "y" in low:
                    self.acc_cols["y"] = c
                elif "z" in low:
                    self.acc_cols["z"] = c

            if pd.api.types.is_numeric_dtype(self.data[c]):
                if c != self.time_col: self.variable_list.addItem(c)

        self.update_max_stats()

        # HUD Limit Updates
        if self.alt_col: self.alt_gauge.update_limits(self.data[self.alt_col].min(), self.data[self.alt_col].max())
        if self.vel_col: self.vel_gauge.update_limits(self.data[self.vel_col].min(), self.data[self.vel_col].max())
        if self.servo_col: self.servo_gauge.update_limits(self.data[self.servo_col].min(),
                                                          self.data[self.servo_col].max())
        if self.yaw_col: self.yaw_gauge.update_limits(self.data[self.yaw_col].min(), self.data[self.yaw_col].max())
        if self.yaw_sp_col: self.yaw_sp_gauge.update_limits(self.data[self.yaw_sp_col].min(),
                                                            self.data[self.yaw_sp_col].max())

        self.slider.setRange(0, len(self.data) - 1)
        self.slider.setEnabled(True)
        self.telemetry.setText(f"LOADED: {path.split('/')[-1]}")

    def update_max_stats(self):
        """Calculates absolute maxima for the summary table."""
        stats = {
            0: self.alt_col,
            1: self.vel_col,
            2: self.acc_cols["x"],
            3: self.acc_cols["y"],
            4: self.acc_cols["z"]
        }
        for row_idx, col_name in stats.items():
            if col_name and col_name in self.data.columns:
                val = self.data[col_name].abs().max()
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem(f"{val:.2f}"))
            else:
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem("N/A"))

    def toggle_playback(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            self.timer.start()
            self.play_btn.setText("⏸ Pause")

    def step_forward(self):
        if self.slider.value() < self.slider.maximum():
            self.slider.setValue(self.slider.value() + 1)
        else:
            self.toggle_playback()

    def toggle_view(self):
        self.stack.setCurrentIndex(1 if self.view_btn.isChecked() else 0)

    def plot_selected(self):
        items = self.variable_list.selectedItems()
        if not items or self.data is None: return

        self.slider.blockSignals(True)
        cols = [i.text() for i in items]
        self.figure.clear()
        self._bg_cache = None

        ax = self.figure.add_subplot(111)
        self.current_ax = ax
        ax.set_facecolor("#121212")
        t_data = self.data[self.time_col].values

        self.intersection_dots = {}
        for c in cols:
            l, = ax.plot(t_data, self.data[c], label=c, lw=1.5)
            d, = ax.plot([], [], 'o', color=l.get_color(), ms=6, mec='white', animated=True)
            self.intersection_dots[c] = d

        ax.legend(loc='upper right', frameon=False)
        self.cursor_line = ax.axvline(t_data[0], color="#00FF00", alpha=0.6, animated=True)
        self.canvas.draw()
        self.slider.blockSignals(False)
        self.slider_moved(self.slider.value())

    def slider_moved(self, i):
        if self.data is None or self.current_ax is None: return
        try:
            row = self.data.iloc[i]
            t_val = row[self.time_col]

            if self._bg_cache is None:
                self._bg_cache = self.canvas.copy_from_bbox(self.current_ax.bbox)
            self.canvas.restore_region(self._bg_cache)
            self.cursor_line.set_xdata([t_val, t_val])
            self.current_ax.draw_artist(self.cursor_line)
            for c, dot in self.intersection_dots.items():
                dot.set_data([t_val], [row[c]])
                self.current_ax.draw_artist(dot)
            self.canvas.blit(self.current_ax.bbox)

            v_max = self.data[self.vel_col].max() if self.vel_col else 1
            v_ratio = abs(row[self.vel_col]) / v_max if self.vel_col and v_max != 0 else 0

            if self.alt_col: self.alt_gauge.set_value(row[self.alt_col], v_ratio)
            if self.vel_col: self.vel_gauge.set_value(row[self.vel_col], v_ratio)
            if self.servo_col: self.servo_gauge.set_value(row[self.servo_col])
            if self.yaw_col: self.yaw_gauge.set_value(row[self.yaw_col])
            if self.yaw_sp_col: self.yaw_sp_gauge.set_value(row[self.yaw_sp_col])

            self.telemetry.setText(f"T: {t_val:.2f}s | ALT: {row.get(self.alt_col, 0):.1f}m")
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    gui = RocketDashboard()
    gui.show()
    sys.exit(app.exec())