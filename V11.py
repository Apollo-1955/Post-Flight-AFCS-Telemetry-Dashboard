import sys
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# =====================================================
# POP OUT GRAPH WINDOW
# =====================================================
class PopoutGraph(QMainWindow):

    def __init__(self, title, time, data):
        super().__init__()

        self.setWindowTitle(title)
        self.resize(1100, 650)

        fig = Figure(facecolor="#151515")
        canvas = FigureCanvasQTAgg(fig)

        ax = fig.add_subplot(111)
        ax.set_facecolor("#151515")
        ax.grid(True, color="#444")

        ax.tick_params(colors="white")
        ax.set_title(title, color="white")

        for spine in ax.spines.values():
            spine.set_color("white")

        ax.plot(time, data, color="cyan")

        self.setCentralWidget(canvas)


# =====================================================
# COLLAPSIBLE SECTION
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

        self.title = title

        layout = QHBoxLayout(self)

        label = QLabel(title)
        label.setFixedWidth(150)
        layout.addWidget(label)

        self.fig = Figure(facecolor="#151515")
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas, 1)

        self.setup_dark()

        self.canvas.mpl_connect(
            "button_press_event",
            self.open_popout
        )

    def setup_dark(self):

        self.ax.set_facecolor("#151515")
        self.ax.grid(True, color="#444")
        self.ax.tick_params(colors="white")

        for s in self.ax.spines.values():
            s.set_color("white")

    def plot(self, t, data):

        self.t = t
        self.data = data

        self.ax.clear()
        self.setup_dark()

        self.ax.plot(t, data, color="cyan")

        self.cursor = self.ax.axvline(
            t[0],
            color="white",
            linestyle="--"
        )

        self.dot, = self.ax.plot(
            [t[0]], [data[0]], "wo"
        )

        self.canvas.draw()

    def update_cursor(self, i):

        self.cursor.set_xdata([self.t[i]])
        self.dot.set_data(
            [self.t[i]],
            [self.data[i]]
        )

        self.canvas.draw_idle()

    def open_popout(self, event):

        if event.inaxes != self.ax:
            return

        self.pop = PopoutGraph(
            self.title,
            self.t,
            self.data
        )
        self.pop.show()


# =====================================================
# 3D ROCKET VIEWER
# =====================================================
class Rocket3D(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        label = QLabel("Rocket Attitude")
        label.setFixedWidth(150)
        layout.addWidget(label)

        self.fig = Figure(facecolor="#151515")
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.ax = self.fig.add_subplot(
            111,
            projection="3d"
        )

        layout.addWidget(self.canvas)

        self.body = np.array([
            [0,0,0],
            [0,0,1.5]
        ])

    def rotation(self,r,p,y):

        r,p,y=np.radians([r,p,y])

        Rx=[[1,0,0],
            [0,np.cos(r),-np.sin(r)],
            [0,np.sin(r),np.cos(r)]]

        Ry=[[np.cos(p),0,np.sin(p)],
            [0,1,0],
            [-np.sin(p),0,np.cos(p)]]

        Rz=[[np.cos(y),-np.sin(y),0],
            [np.sin(y),np.cos(y),0],
            [0,0,1]]

        return np.dot(Rz,np.dot(Ry,Rx))

    def update_attitude(self,roll,pitch,yaw):

        self.ax.cla()

        R=self.rotation(roll,pitch,yaw)
        rot=self.body@np.array(R).T

        self.ax.plot(
            rot[:,0],
            rot[:,1],
            rot[:,2],
            linewidth=4,
            color="cyan"
        )

        self.ax.set_xlim([-1,1])
        self.ax.set_ylim([-1,1])
        self.ax.set_zlim([0,2])

        self.canvas.draw_idle()


# =====================================================
# MAIN DASHBOARD
# =====================================================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Flight Dashboard")
        self.resize(1550,950)

        main=QWidget()
        self.setCentralWidget(main)
        layout=QVBoxLayout(main)

        # Buttons
        btns=QHBoxLayout()
        self.load=QPushButton("Load CSV")
        self.play=QPushButton("Play")

        btns.addWidget(self.load)
        btns.addWidget(self.play)
        layout.addLayout(btns)

        # Scroll dashboard
        self.scroll=QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container=QWidget()
        self.vbox=QVBoxLayout(self.container)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # timeline
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

        self.apply_dark()

    def apply_dark(self):
        self.setStyleSheet("""
            QWidget{background:#121212;color:white;}
            QPushButton{
                background:#1f1f1f;
                padding:6px;
                border-radius:6px;
            }
        """)

    def detect(self,keys):
        for c in self.data.columns:
            if any(k in c.lower() for k in keys):
                return c
        return None

    def clear_dashboard(self):
        while self.vbox.count():
            w=self.vbox.takeAt(0).widget()
            if w:
                w.deleteLater()

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

        # 3D attitude
        r=self.detect(["roll"])
        p=self.detect(["pitch"])
        y=self.detect(["yaw"])

        if r and p and y:
            box=CollapsibleBox("Rocket Attitude")
            self.rocket3d=Rocket3D()
            box.content_layout.addWidget(
                self.rocket3d
            )
            self.roll=self.data[r].values
            self.pitch=self.data[p].values
            self.yaw=self.data[y].values
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

    def update_all(self,i):

        for c in self.cards:
            c.update_cursor(i)

        if hasattr(self,"rocket3d"):
            self.rocket3d.update_attitude(
                self.roll[i],
                self.pitch[i],
                self.yaw[i]
            )

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