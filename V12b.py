import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D


# =====================================================
# POP OUT WINDOW
# =====================================================
class PopoutGraph(QMainWindow):

    def __init__(self, time, data, title):
        super().__init__()

        self.setWindowTitle(title)
        self.resize(900,600)

        fig = Figure(facecolor="#111")
        canvas = FigureCanvas(fig)
        self.setCentralWidget(canvas)

        ax = fig.add_subplot(111)
        ax.set_facecolor("#111")
        ax.grid(True,color="#333")
        ax.tick_params(colors="white")

        # Move title to left side
        ax.text(-0.05, 0.5, title, transform=ax.transAxes, color="white",
                fontsize=12, rotation=90, va="center", ha="right")

        ax.plot(time,data)

        fig.tight_layout()
        canvas.draw()


# =====================================================
# GRAPH CARD
# =====================================================
class GraphCard(QGroupBox):

    def __init__(self,title):
        super().__init__()

        layout = QVBoxLayout(self)

        self.figure = Figure(facecolor="#111")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#111")

        self.time=None
        self.data=None

        self.cursor=None
        self.dot=None

        self.graph_name = title

        # CLICK TO POP OUT
        self.canvas.mpl_connect(
            "button_press_event",
            self.open_popout
        )

    def plot(self,time,data,label):

        self.ax.clear()

        self.ax.set_facecolor("#111")
        self.ax.grid(True,color="#333")
        self.ax.tick_params(colors="white")

        # Add graph name on the left side
        self.ax.text(-0.05, 0.5, label, transform=self.ax.transAxes,
                     color="white", fontsize=10, rotation=90,
                     va="center", ha="right")

        self.time=time
        self.data=data

        self.ax.plot(time,data)

        self.cursor=self.ax.axvline(time[0],
                                   linestyle="--",
                                   color="white")

        self.dot,=self.ax.plot(
            [time[0]],[data[0]],
            marker="o",
            color="cyan"
        )

        # Adjust layout to prevent clipping
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.1)
        self.canvas.draw()

    def update_cursor(self,t,index):
        if self.data is None:
            return

        self.cursor.set_xdata([t,t])
        self.dot.set_data([t],[self.data[index]])
        self.canvas.draw_idle()

    def open_popout(self,event):
        if self.time is None:
            return
        self.pop=PopoutGraph(
            self.time,
            self.data,
            self.graph_name
        )
        self.pop.show()


# =====================================================
# COLLAPSIBLE SECTION
# =====================================================
class CollapsibleBox(QWidget):

    def __init__(self,title):
        super().__init__()

        self.layout=QVBoxLayout(self)

        self.toggle=QPushButton(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(True)

        self.content=QWidget()
        self.content_layout=QVBoxLayout(self.content)

        self.layout.addWidget(self.toggle)
        self.layout.addWidget(self.content)

        self.toggle.clicked.connect(self.toggle_content)

    def toggle_content(self):
        self.content.setVisible(self.toggle.isChecked())


# =====================================================
# 3D ROCKET ATTITUDE VIEWER
# =====================================================
class AttitudeViewer(QGroupBox):

    def __init__(self):
        super().__init__("3D Rocket Attitude")

        layout=QVBoxLayout(self)

        self.figure=Figure(facecolor="#111")
        self.canvas=FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax=self.figure.add_subplot(111,projection="3d")

    def update(self,pitch,roll,yaw):

        self.ax.clear()
        self.ax.set_facecolor("#111")

        length=1

        Rx=np.array([
            [1,0,0],
            [0,np.cos(roll),-np.sin(roll)],
            [0,np.sin(roll),np.cos(roll)]
        ])

        Ry=np.array([
            [np.cos(pitch),0,np.sin(pitch)],
            [0,1,0],
            [-np.sin(pitch),0,np.cos(pitch)]
        ])

        Rz=np.array([
            [np.cos(yaw),-np.sin(yaw),0],
            [np.sin(yaw),np.cos(yaw),0],
            [0,0,1]
        ])

        R=Rz@Ry@Rx

        vec=R@np.array([0,0,length])

        self.ax.plot(
            [0,vec[0]],
            [0,vec[1]],
            [0,vec[2]],
            linewidth=4
        )

        self.ax.set_xlim([-1,1])
        self.ax.set_ylim([-1,1])
        self.ax.set_zlim([-1,1])

        self.canvas.draw_idle()


# =====================================================
# MAIN DASHBOARD
# =====================================================
class RocketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Rocket Dashboard")
        self.resize(1500,900)

        self.data=None
        self.cards=[]
        self.attitude=None

        main=QWidget()
        self.setCentralWidget(main)
        layout=QVBoxLayout(main)

        # CONTROLS
        controls=QHBoxLayout()

        self.load_btn=QPushButton("Load CSV")
        self.play_btn=QPushButton("Play")
        self.pause_btn=QPushButton("Pause")

        controls.addWidget(self.load_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)

        layout.addLayout(controls)

        # SCROLL
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)

        self.container=QWidget()
        self.dashboard=QVBoxLayout(self.container)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        # SLIDER
        self.slider=QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.slider)

        # TIMER
        self.timer=QTimer()
        self.timer.timeout.connect(self.animate)

        self.play_btn.clicked.connect(
            lambda:self.timer.start(20))
        self.pause_btn.clicked.connect(
            self.timer.stop)

        self.slider.valueChanged.connect(
            self.update_all)

        self.load_btn.clicked.connect(
            self.load_csv)

        self.apply_dark()

    # -------------------------------------------------
    def apply_dark(self):
        self.setStyleSheet("""
        QWidget{background:#121212;color:white;}
        QPushButton{background:#1f1f1f;padding:6px;}
        QGroupBox{border:1px solid #333;}
        """)

    # -------------------------------------------------
    def detect_phases(self,alt):

        vel=np.gradient(alt)

        phases=[]

        for v in vel:
            if v>5:
                phases.append("BOOST")
            elif v>0:
                phases.append("COAST")
            elif v<-2:
                phases.append("DESCENT")
            else:
                phases.append("LANDED")

        return phases

    # -------------------------------------------------
    def load_csv(self):

        path,_=QFileDialog.getOpenFileName(
            self,"Open CSV","","CSV (*.csv)")

        if not path:
            return

        self.data=pd.read_csv(path)

        time=[c for c in self.data.columns
              if "time" in c.lower()][0]

        t=self.data[time].values

        numeric=self.data.select_dtypes(
            include='number')

        section=CollapsibleBox("Flight Data")
        self.dashboard.addWidget(section)

        self.cards.clear()

        for col in numeric.columns:
            if col==time:
                continue

            card=GraphCard(col)
            card.plot(t,
                      numeric[col].values,
                      col)

            section.content_layout.addWidget(card)
            self.cards.append(card)

        # ATTITUDE VIEWER
        self.attitude=AttitudeViewer()
        self.dashboard.addWidget(self.attitude)

        self.slider.setMaximum(len(t)-1)

    # -------------------------------------------------
    def update_all(self,index):

        if self.data is None:
            return

        time=[c for c in self.data.columns
              if "time" in c.lower()][0]

        t=self.data[time].values[index]

        for c in self.cards:
            c.update_cursor(t,index)

        try:
            pitch=self.data.filter(
                regex="pitch",axis=1).values[index][0]
            roll=self.data.filter(
                regex="roll",axis=1).values[index][0]
            yaw=self.data.filter(
                regex="yaw",axis=1).values[index][0]

            self.attitude.update(
                np.radians(pitch),
                np.radians(roll),
                np.radians(yaw)
            )
        except:
            pass

    # -------------------------------------------------
    def animate(self):

        v=self.slider.value()+1

        if v>=self.slider.maximum():
            self.timer.stop()
            return

        self.slider.setValue(v)


# =====================================================
if __name__=="__main__":
    app=QApplication(sys.argv)
    win=RocketDashboard()
    win.show()
    sys.exit(app.exec())