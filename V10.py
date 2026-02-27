import sys
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# =====================================================
# COLLAPSIBLE BOX
# =====================================================
class CollapsibleBox(QWidget):

    def __init__(self, title):
        super().__init__()

        self.button = QPushButton("▼ " + title)
        self.button.setCheckable(True)
        self.button.setChecked(True)
        self.button.clicked.connect(self.toggle)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.addWidget(self.content)

    def toggle(self):
        visible = self.button.isChecked()
        self.content.setVisible(visible)
        arrow = "▼ " if visible else "▶ "
        self.button.setText(arrow + self.button.text()[2:])


# =====================================================
# GRAPH CARD
# =====================================================
class GraphCard(QWidget):

    def __init__(self, title):
        super().__init__()

        layout = QHBoxLayout(self)

        label = QLabel(title)
        label.setFixedWidth(140)
        layout.addWidget(label)

        self.fig = Figure(facecolor="#151515")
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_facecolor("#151515")
        self.ax.grid(True)

        layout.addWidget(self.canvas, 1)

    def plot(self, t, data):

        self.t = t
        self.data = data

        self.ax.clear()
        self.ax.plot(t, data)

        self.cursor = self.ax.axvline(t[0])
        self.dot, = self.ax.plot(
            [t[0]], [data[0]], "o"
        )

        self.canvas.draw()

    def update_cursor(self, i):

        self.cursor.set_xdata([self.t[i]])
        self.dot.set_data(
            [self.t[i]],
            [self.data[i]]
        )

        self.canvas.draw_idle()


# =====================================================
# 3D ROCKET VIEWER
# =====================================================
class Rocket3D(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        label = QLabel("Rocket Attitude")
        label.setFixedWidth(140)
        layout.addWidget(label)

        self.fig = Figure(facecolor="#151515")
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.ax = self.fig.add_subplot(
            111,
            projection="3d"
        )

        layout.addWidget(self.canvas)

        self.init_scene()

    def init_scene(self):

        self.ax.set_xlim([-1,1])
        self.ax.set_ylim([-1,1])
        self.ax.set_zlim([0,2])

        self.body = np.array([
            [0,0,0],
            [0,0,1.5]
        ])

    def rotation_matrix(self, r,p,y):

        r,p,y = np.radians([r,p,y])

        Rx=np.array([[1,0,0],
                     [0,np.cos(r),-np.sin(r)],
                     [0,np.sin(r),np.cos(r)]])

        Ry=np.array([[np.cos(p),0,np.sin(p)],
                     [0,1,0],
                     [-np.sin(p),0,np.cos(p)]])

        Rz=np.array([[np.cos(y),-np.sin(y),0],
                     [np.sin(y),np.cos(y),0],
                     [0,0,1]])

        return Rz@Ry@Rx

    def update_attitude(self, roll, pitch, yaw):

        self.ax.cla()
        self.init_scene()

        R=self.rotation_matrix(
            roll,pitch,yaw
        )

        rot=self.body@R.T

        self.ax.plot(
            rot[:,0],
            rot[:,1],
            rot[:,2],
            linewidth=4
        )

        self.canvas.draw_idle()


# =====================================================
# MAIN DASHBOARD
# =====================================================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rocket Flight Replay")
        self.resize(1500,950)

        main=QWidget()
        self.setCentralWidget(main)
        layout=QVBoxLayout(main)

        # buttons
        btns=QHBoxLayout()
        self.load=QPushButton("Load CSV")
        self.play=QPushButton("Play")

        btns.addWidget(self.load)
        btns.addWidget(self.play)

        layout.addLayout(btns)

        self.scroll=QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container=QWidget()
        self.vbox=QVBoxLayout(self.container)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.slider=QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.slider)

        self.timer=QTimer()
        self.timer.timeout.connect(self.animate)

        self.load.clicked.connect(self.load_csv)
        self.play.clicked.connect(
            lambda:self.timer.start(30)
        )
        self.slider.valueChanged.connect(
            self.update_all
        )

    # =========================
    def detect(self,keys):

        for c in self.data.columns:
            name=c.lower()
            if any(k in name for k in keys):
                return c
        return None

    # =========================
    def clear_dashboard(self):

        while self.vbox.count():
            item=self.vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # =========================
    def load_csv(self):

        path,_=QFileDialog.getOpenFileName(
            self,"CSV","","*.csv"
        )
        if not path:
            return

        self.clear_dashboard()

        self.data=pd.read_csv(path)

        tcol=self.detect(["time"])
        if not tcol:
            QMessageBox.warning(
                self,"Error",
                "No time column found"
            )
            return

        self.time=self.data[tcol].values

        # attitude safe detection
        r=self.detect(["roll"])
        p=self.detect(["pitch"])
        y=self.detect(["yaw"])

        if r and p and y:
            self.roll=self.data[r].values
            self.pitch=self.data[p].values
            self.yaw=self.data[y].values

            box=CollapsibleBox(
                "Rocket Attitude"
            )

            self.rocket3d=Rocket3D()
            box.content_layout.addWidget(
                self.rocket3d
            )

            self.vbox.addWidget(box)

        # graphs
        self.cards=[]
        num=self.data.select_dtypes(
            include="number"
        )

        gbox=CollapsibleBox("Telemetry")

        for col in num.columns:
            if col==tcol:
                continue

            card=GraphCard(col)
            card.plot(
                self.time,
                num[col].values
            )

            gbox.content_layout.addWidget(card)
            self.cards.append(card)

        self.vbox.addWidget(gbox)

        self.slider.setMaximum(
            len(self.time)-1
        )

    # =========================
    def update_all(self,i):

        for c in self.cards:
            c.update_cursor(i)

        if hasattr(self,"rocket3d"):
            self.rocket3d.update_attitude(
                self.roll[i],
                self.pitch[i],
                self.yaw[i]
            )

    # =========================
    def animate(self):

        v=self.slider.value()+1
        if v>=self.slider.maximum():
            self.timer.stop()
            return

        self.slider.setValue(v)


# =====================================================
app=QApplication(sys.argv)
win=RocketDashboard()
win.show()
sys.exit(app.exec())