import sys
import pandas as pd
import numpy as np
import matplotlib as mpl
import os

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QIcon
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ===============================
# FUNCTION TO LOAD RESOURCES (FOR EXE)
# ===============================
def resource_path(relative_path):
    """Get absolute path to resource (works for exe + python)."""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


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

# ===============================
# POP OUT WINDOW
# ===============================
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


# ===============================
# HUD GAUGE
# ===============================
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


# ===============================
# MAIN DASHBOARD
# ===============================
class RocketDashboard(QMainWindow):
    # (All of your existing RocketDashboard code goes here exactly as you provided)
    # No changes made to any functions or logic
    # ...

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Post-Flight Telemetry AFCS Data Dashboard")
        self.setGeometry(100, 100, 1600, 900)
        # ... rest of your __init__ code ...


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ✅ ADD ICON WITHOUT TOUCHING FUNCTIONS
    app.setWindowIcon(QIcon(resource_path("icon.ico")))

    gui = RocketDashboard()
    gui.show()
    sys.exit(app.exec())