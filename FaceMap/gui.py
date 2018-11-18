import sys
import os
import shutil
import time
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph import GraphicsScene
import pims
from FaceMap import facemap

class MainW(QtGui.QMainWindow):
    def __init__(self):
        super(MainW, self).__init__()
        pg.setConfigOptions(imageAxisOrder='row-major')
        self.setGeometry(70,70,1070,1070)
        self.setWindowTitle('FaceMap')
        self.setStyleSheet("background-color: black;")
        self.cwidget = QtGui.QWidget(self)
        self.setCentralWidget(self.cwidget)
        self.l0 = QtGui.QGridLayout()
        #layout = QtGui.QFormLayout()
        self.cwidget.setLayout(self.l0)
        #self.p0 = pg.ViewBox(lockAspect=False,name='plot1',border=[100,100,100],invertY=True)
        self.win = pg.GraphicsLayoutWidget()
        # --- cells image
        self.win = pg.GraphicsLayoutWidget()
        self.win.move(600,0)
        self.win.resize(1000,500)
        self.l0.addWidget(self.win,0,0,13,14)
        layout = self.win.ci.layout
        # A plot area (ViewBox + axes) for displaying the image
        self.p0 = self.win.addViewBox(lockAspect=True,row=0,col=0,invertY=True)
        #self.p0.setMouseEnabled(x=False,y=False)
        self.p0.setMenuEnabled(False)
        self.pimg = pg.ImageItem()
        self.p0.addItem(self.pimg)
        self.p1 = self.win.addPlot(name='plot1',row=1,col=0)
        self.p1.setMouseEnabled(x=True,y=False)
        self.p1.setMenuEnabled(False)
        #self.p1.autoRange(padding=0.01)
        self.p2 = self.win.addPlot(name='plot2',row=2,col=0)
        self.p2.setMouseEnabled(x=True,y=False)
        self.p2.setMenuEnabled(False)
        #self.p2.autoRange(padding=0.01)
        self.win.ci.layout.setRowStretchFactor(0,5)
        self.movieLabel = QtGui.QLabel("No movie chosen")
        self.movieLabel.setStyleSheet("color: white;")
        self.movieLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.nframes = 0
        self.cframe = 0
        self.createButtons()
        # create ROI chooser
        self.l0.addWidget(QtGui.QLabel(''),2,0,1,2)
        qlabel = QtGui.QLabel(self)
        qlabel.setText("<font color='white'>Selected ROI:</font>")
        self.l0.addWidget(qlabel,3,0,1,2)
        self.ROIedit = QtGui.QLineEdit(self)
        self.ROIedit.setValidator(QtGui.QIntValidator(0,10000))
        self.ROIedit.setText('0')
        self.ROIedit.setFixedWidth(45)
        self.ROIedit.setAlignment(QtCore.Qt.AlignRight)
        self.ROIedit.returnPressed.connect(self.number_chosen)
        self.l0.addWidget(self.ROIedit, 4,0,1,1)
        # create frame slider
        self.frameLabel = QtGui.QLabel("Current frame:")
        self.frameLabel.setStyleSheet("color: white;")
        self.frameNumber = QtGui.QLabel("0")
        self.frameNumber.setStyleSheet("color: white;")
        self.frameSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        #self.frameSlider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.frameSlider.setTickInterval(5)
        self.frameSlider.setTracking(False)
        self.frameDelta = 10
        self.l0.addWidget(QtGui.QLabel(''),12,0,1,1)
        self.l0.setRowStretch(12,1)
        self.l0.addWidget(self.frameLabel, 13,0,1,2)
        self.l0.addWidget(self.frameNumber, 14,0,1,2)
        self.l0.addWidget(self.frameSlider, 13,2,14,13)
        self.l0.addWidget(QtGui.QLabel(''),14,1,1,1)
        ll = QtGui.QLabel('(when paused, left/right arrow keys can move slider)')
        ll.setStyleSheet("color: white;")
        self.l0.addWidget(ll,16,0,1,3)
        #speedLabel = QtGui.QLabel("Speed:")
        #self.speedSpinBox = QtGui.QSpinBox()
        #self.speedSpinBox.setRange(1, 9999)
        #self.speedSpinBox.setValue(100)
        #self.speedSpinBox.setSuffix("%")
        self.frameSlider.valueChanged.connect(self.go_to_frame)
        self.l0.addWidget(self.movieLabel,0,0,1,5)
        self.updateFrameSlider()
        self.updateButtons()
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.next_frame)
        self.cframe = 0
        self.loaded = False
        self.Floaded = False
        self.wraw = False
        self.win.scene().sigMouseClicked.connect(self.plot_clicked)
        self.win.show()
        self.show()
        # if not a combined recording, automatically open binary

    def open(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                            "Open movie file")
        # load ops in same folder
        if fileName:
            print(fileName[0])
            self.openFile([fileName[0]])

    #def open_folder(self):
    #    fileName = QtGui.QFileDialog.getOpenFolder(self,
    #                        "Open movie folder")
        # load ops in same folder
    #    if fileName:
    #        print(fileName[0])
    #        os.path.
    #        self.openFile(fileName[0], False)

    def openFile(self, fileNames):
        try:
            v = []
            nframes = 0
            iframes = []
            for file in fileNames:
                v.append(pims.Video(file))
                iframes.append(len(v[-1]))
                nframes += len(v[-1])
            good = True
        except Exception as e:
            print("ERROR: not a supported movie file")
            print(e)
            good = False
        if good:
            self.v = v
            self.filenames = fileNames
            self.nframes = nframes
            self.iframes = np.array(iframes).astype(int)
            self.Ly = self.v[0].frame_shape[0]
            self.Lx = self.v[0].frame_shape[1]
            self.p1.clear()
            self.p2.clear()
            self.ichosen = 0
            self.ROIedit.setText('0')
            # get scaling from 100 random frames
            rperm = np.random.permutation(nframes)
            frames = np.zeros((self.Ly,self.Lx,100))
            for r in range(100):
                frames[:,:,r] = np.array(self.v[0][rperm[r]]).mean(axis=-1)
            self.srange = frames.mean() + frames.std()*np.array([-3,3])
            #self.srange = [np.percentile(frames.flatten(),8), np.percentile(frames.flatten(),99)]
            self.movieLabel.setText(self.filenames[0])
            self.nbytesread = 2 * self.Ly * self.Lx
            self.frameDelta = int(np.maximum(5,self.nframes/200))
            self.frameSlider.setSingleStep(self.frameDelta)
            if self.nframes > 0:
                self.updateFrameSlider()
                self.updateButtons()
            # plot ops X-Y offsets
            #
            # self.p1.plot(self.yoff, pen='g')
            # self.p1.plot(self.xoff, pen='y')
            # self.p1.setRange(xRange=(0,self.nframes),
            #                  yRange=(np.minimum(self.yoff.min(),self.xoff.min()),
            #                          np.maximum(self.yoff.max(),self.xoff.max())),
            #                  padding=0.0)
            # self.p1.setLimits(xMin=0,xMax=self.nframes)
            # self.scatter1 = pg.ScatterPlotItem()
            # self.p1.addItem(self.scatter1)
            # self.scatter1.setData([self.cframe,self.cframe],
            #                       [self.yoff[self.cframe],self.xoff[self.cframe]],
            #                       size=10,brush=pg.mkBrush(255,0,0))
            self.cframe = -1
            self.loaded = True
            self.next_frame()

    def keyPressEvent(self, event):
        bid = -1
        if self.playButton.isEnabled():
            if event.modifiers() !=  QtCore.Qt.ShiftModifier:
                if event.key() == QtCore.Qt.Key_Left:
                    self.cframe -= self.frameDelta
                    self.cframe  = np.maximum(0, np.minimum(self.nframes-1, self.cframe))
                    self.frameSlider.setValue(self.cframe)
                elif event.key() == QtCore.Qt.Key_Right:
                    self.cframe += self.frameDelta
                    self.cframe  = np.maximum(0, np.minimum(self.nframes-1, self.cframe))
                    self.frameSlider.setValue(self.cframe)
        if event.modifiers() != QtCore.Qt.ShiftModifier:
            if event.key() == QtCore.Qt.Key_Space:
                if self.playButton.isEnabled():
                    # then play
                    self.start()
                else:
                    self.pause()

    def number_chosen(self):
        if self.Floaded:
            self.ichosen = int(self.ROIedit.text())
            if self.ichosen >= len(self.stat):
                self.ichosen = len(self.stat) - 1
            self.cell_mask()
            self.p2.clear()
            self.ft = self.Fcell[self.ichosen,:]
            self.p2.plot(self.ft,pen='b')
            self.p2.setRange(yRange=(self.ft.min(),self.ft.max()))
            self.scatter2 = pg.ScatterPlotItem()
            self.p2.addItem(self.scatter2)
            self.scatter2.setData([self.cframe],[self.ft[self.cframe]],size=10,brush=pg.mkBrush(255,0,0))
            self.p2.setXLink('plot1')
            self.jump_to_frame()
            self.show()

    def plot_clicked(self,event):
        items = self.win.scene().items(event.scenePos())
        posx  = 0
        posy  = 0
        iplot = 0
        zoom = False
        zoomImg = False
        choose = False
        if self.loaded:
            for x in items:
                if x==self.p1:
                    vb = self.p1.vb
                    pos = vb.mapSceneToView(event.scenePos())
                    posx = pos.x()
                    iplot = 1
                elif x==self.p2 and self.Floaded:
                    vb = self.p1.vb
                    pos = vb.mapSceneToView(event.scenePos())
                    posx = pos.x()
                    iplot = 2
                elif x==self.p0:
                    if event.button()==1:
                        if event.double():
                            zoomImg=True
                if iplot==1 or iplot==2:
                    if event.button()==1:
                        if event.double():
                            zoom=True
                        else:
                            choose=True
        if zoomImg:
            if not self.wraw:
                self.p0.setRange(xRange=(0,self.Lx),yRange=(0,self.Ly))
            else:
                self.p0.setRange(xRange=(0,self.Lx*2+max(10,int(self.Lx*.05))),yRange=(0,self.Ly))
        if zoom:
            self.p1.setRange(xRange=(0,self.nframes))
        if choose:
            if self.playButton.isEnabled():
                self.cframe = np.maximum(0, np.minimum(self.nframes-1, int(np.round(posx))))
                self.frameSlider.setValue(self.cframe)
                #self.jump_to_frame()

    def cell_mask(self):
        #self.cmask = np.zeros((self.Ly,self.Lx,3),np.float32)
        self.yext = self.stat[self.ichosen]['yext']
        self.xext = self.stat[self.ichosen]['xext']
        #self.cmask[self.yext,self.xext,2] = (self.srange[1]-self.srange[0])/2 * np.ones((self.yext.size,),np.float32)

    def go_to_frame(self):
        self.cframe = int(self.frameSlider.value())
        self.jump_to_frame()

    def fitToWindow(self):
        self.movieLabel.setScaledContents(self.fitCheckBox.isChecked())

    def updateFrameSlider(self):
        self.frameSlider.setMaximum(self.nframes-1)
        self.frameSlider.setMinimum(0)
        self.frameLabel.setEnabled(True)
        self.frameSlider.setEnabled(True)

    def updateButtons(self):
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setChecked(True)

    def createButtons(self):
        iconSize = QtCore.QSize(30, 30)
        openButton = QtGui.QToolButton()
        openButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton))
        openButton.setIconSize(iconSize)
        openButton.setToolTip("Open binary file")
        openButton.clicked.connect(self.open)

        self.process = QtGui.QPushButton("Process data")
        self.process.clicked.connect(self.process_ROIs)

        self.playButton = QtGui.QToolButton()
        self.playButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        self.playButton.setIconSize(iconSize)
        self.playButton.setToolTip("Play")
        self.playButton.setCheckable(True)
        self.playButton.clicked.connect(self.start)

        self.pauseButton = QtGui.QToolButton()
        self.pauseButton.setCheckable(True)
        self.pauseButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPause))
        self.pauseButton.setIconSize(iconSize)
        self.pauseButton.setToolTip("Pause")
        self.pauseButton.clicked.connect(self.pause)

        btns = QtGui.QButtonGroup(self)
        btns.addButton(self.playButton,0)
        btns.addButton(self.pauseButton,1)
        btns.setExclusive(True)

        quitButton = QtGui.QToolButton()
        quitButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogCloseButton))
        quitButton.setIconSize(iconSize)
        quitButton.setToolTip("Quit")
        quitButton.clicked.connect(self.close)

        self.l0.addWidget(openButton,1,0,1,1)
        self.l0.addWidget(self.process,2,0,1,1)
        self.l0.addWidget(self.playButton,15,0,1,1)
        self.l0.addWidget(self.pauseButton,15,1,1,1)
        #self.l0.addWidget(quitButton,0,1,1,1)
        self.playButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setChecked(True)

    def jump_to_frame(self):
        if self.playButton.isEnabled():
            self.cframe = np.maximum(0, np.minimum(self.nframes-1, self.cframe))
            self.cframe = int(self.cframe)
            self.cframe -= 1
            self.next_frame()

    def next_frame(self):
        # loop after video finishes
        self.cframe+=1
        if self.cframe > self.nframes - 1:
            self.cframe = 0
        self.img = np.array(self.v[0][self.cframe])
        #if self.Floaded:
        #    self.img[self.yext,self.xext,0] = self.srange[0]
        #    self.img[self.yext,self.xext,1] = self.srange[0]
        #    self.img[self.yext,self.xext,2] = (self.srange[1]) * np.ones((self.yext.size,),np.float32)
        self.pimg.setImage(self.img)
        self.pimg.setLevels(self.srange)
        self.frameSlider.setValue(self.cframe)
        self.frameNumber.setText(str(self.cframe))
        #self.scatter1.setData([self.cframe,self.cframe],
        #                      [self.yoff[self.cframe],self.xoff[self.cframe]],
        #                      size=10,brush=pg.mkBrush(255,0,0))

    def start(self):
        if self.cframe < self.nframes - 1:
            #print('playing')
            self.playButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.frameSlider.setEnabled(False)
            self.updateTimer.start(25)

    def pause(self):
        self.updateTimer.stop()
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.frameSlider.setEnabled(True)
        #print('paused')

    def process_ROIs(self):
        self.playButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.frameSlider.setEnabled(False)
        facemap.run(self, self.filenames)




def run():
    # Always start by initializing Qt (only once per application)
    app = QtGui.QApplication(sys.argv)
    # icon_path = os.path.join(
    #     os.path.dirname(os.path.realpath(__file__)), "logo/logo.png"
    # )
    # app_icon = QtGui.QIcon()
    # app_icon.addFile(icon_path, QtCore.QSize(16, 16))
    # app_icon.addFile(icon_path, QtCore.QSize(24, 24))
    # app_icon.addFile(icon_path, QtCore.QSize(32, 32))
    # app_icon.addFile(icon_path, QtCore.QSize(48, 48))
    # app_icon.addFile(icon_path, QtCore.QSize(96, 96))
    # app_icon.addFile(icon_path, QtCore.QSize(256, 256))
    # app.setWindowIcon(app_icon)
    GUI = MainW()
    #p = GUI.palette()
    ret = app.exec_()
    # GUI.save_gui_data()
    sys.exit(ret)


# run()
