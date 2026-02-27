import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RocketDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rocket Telemetry Dashboard")
        self.setGeometry(100, 100, 1400, 900)

        self.data = None
        self.current_index = 0

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # ===== Top Bar =====
        top_layout = QHBoxLayout()

        self.open_button = QPushButton("Open Flight CSV")
        self.open_button.clicked.connect(self.open_file)
        self.open_button.setStyleSheet("padding: 8px; font-size: 14px;")

        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: gray;")

        top_layout.addWidget(self.open_button)
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        # ===== Graph Grid =====
        self.figure = Figure(facecolor="#121212")
        self.canvas = FigureCanvas(self.figure)

        self.ax_alt = self.figure.add_subplot(221)
        self.ax_pitch = self.figure.add_subplot(222)
        self.ax_roll = self.figure.add_subplot(223)
        self.ax_velocity = self.figure.add_subplot(224)

        self.setup_axes()

        main_layout.addWidget(self.canvas)

        # ===== Metrics Panel =====
        metrics_layout = QHBoxLayout()

        self.metric_time = QLabel("Time: -")
        self.metric_alt = QLabel("Altitude: -")
        self.metric_vel = QLabel("Velocity: -")
        self.metric_pitch = QLabel("Pitch: -")
        self.metric_roll = QLabel("Roll: -")

        for label in [self.metric_time, self.metric_alt, self.metric_vel,
                      self.metric_pitch, self.metric_roll]:
            label.setFont(QFont("Arial", 11))
            label.setStyleSheet("color: white; padding: 4px;")
            metrics_layout.addWidget(label)

        main_layout.addLayout(metrics_layout)

        # ===== Timeline Slider =====
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.update_metrics)
        self.slider.setEnabled(False)
        main_layout.addWidget(self.slider)

        self.setCentralWidget(main_widget)

        # Dark theme styling
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QPushButton { background-color: #1f1f1f; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #2c2c2c; }
        """)

    def setup_axes(self):
        axes = [self.ax_alt, self.ax_pitch, self.ax_roll, self.ax_velocity]

        for ax in axes:
            ax.set_facecolor("#1e1e1e")
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.title.set_color('white')
            ax.grid(True, linestyle="--", alpha=0.3)

        self.ax_alt.set_title("Altitude vs Time")
        self.ax_pitch.set_title("Pitch vs Time")
        self.ax_roll.set_title("Roll vs Time")
        self.ax_velocity.set_title("Velocity vs Time")

        self.figure.tight_layout()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )

        if file_path:
            self.file_label.setText(file_path.split("/")[-1])
            self.load_data(file_path)
            self.plot_data()
            self.slider.setEnabled(True)

    def load_data(self, path):
        self.data = pd.read_csv(path)

        # Ensure required columns exist
        required = ["time", "pitch", "roll", "yaw", "altitude", "velocity"]
        for col in required:
            if col not in self.data.columns:
                raise ValueError(f"Missing column: {col}")

        self.slider.setMaximum(len(self.data) - 1)
        self.slider.setValue(0)

    def plot_data(self):
        self.ax_alt.clear()
        self.ax_pitch.clear()
        self.ax_roll.clear()
        self.ax_velocity.clear()

        self.setup_axes()

        self.ax_alt.plot(self.data["time"], self.data["altitude"])
        self.ax_pitch.plot(self.data["time"], self.data["pitch"])
        self.ax_roll.plot(self.data["time"], self.data["roll"])
        self.ax_velocity.plot(self.data["time"], self.data["velocity"])

        self.canvas.draw()

    def update_metrics(self, index):
        if self.data is None:
            return

        row = self.data.iloc[index]

        self.metric_time.setText(f"Time: {row['time']:.2f}s")
        self.metric_alt.setText(f"Altitude: {row['altitude']:.2f} m")
        self.metric_vel.setText(f"Velocity: {row['velocity']:.2f} m/s")
        self.metric_pitch.setText(f"Pitch: {row['pitch']:.2f}°")
        self.metric_roll.setText(f"Roll: {row['roll']:.2f}°")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketDashboard()
    window.show()
    sys.exit(app.exec())
