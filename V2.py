import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QListWidget, QLabel,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RocketDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Flight Analysis Dashboard")
        self.setGeometry(200, 100, 1200, 800)

        self.data = None

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout()
        central_widget.setLayout(self.layout)

        # Left control panel
        self.control_panel = QVBoxLayout()

        self.load_button = QPushButton("Load Flight CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.plot_button = QPushButton("Plot Selected Data")
        self.plot_button.clicked.connect(self.plot_selected)

        self.label = QLabel("Select variables to plot:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.variable_list = QListWidget()
        self.variable_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.control_panel.addWidget(self.load_button)
        self.control_panel.addWidget(self.label)
        self.control_panel.addWidget(self.variable_list)
        self.control_panel.addWidget(self.plot_button)

        # Matplotlib figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Add layouts
        self.layout.addLayout(self.control_panel, 1)
        self.layout.addWidget(self.canvas, 4)

        self.apply_modern_style()

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

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Flight CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.variable_list.clear()

                # Detect numeric columns automatically
                numeric_columns = self.data.select_dtypes(include='number').columns

                # Remove time from selection list
                for col in numeric_columns:
                    if col != "time":
                        self.variable_list.addItem(col)

                QMessageBox.information(self, "Success", "CSV Loaded Successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

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

        time = self.data["time"]

        for item in selected_items:
            column = item.text()
            ax.plot(time, self.data[column], label=column)

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Value")
        ax.set_title("Flight Data vs Time")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketDashboard()
    window.show()
    sys.exit(app.exec())