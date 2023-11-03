from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QFileDialog, QLabel, QFileDialog, QMessageBox, 
                             QProgressDialog, QVBoxLayout, QDialog, QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

def readSWC(swc_path, mode='simple'):  # pandas DataFrame
    n_skip = 0
    with open(swc_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#"):
                n_skip += 1
            else:
                break
    # names = ["##n", "type", "x", "y", "z", "r", "parent", "seg_id", "level", "mode", "timestamp", "teraflyindex"]
    names = ["##n", "type", "x", "y", "z", "r", "parent"]
    used_cols = [0, 1, 2, 3, 4, 5, 6]
    if mode == 'simple':
        pass
    df = pd.read_csv(swc_path, index_col=0, skiprows=n_skip, sep=" ",
                     usecols=used_cols,
                     names=names
                     )
    return df

def get_degree(tswc):   # Degree of node: the number of nodes connected to it
    tswc['degree'] = tswc['parent'].isin(tswc.index).astype('int')
    # print(tswc['degree'])
    n_child = tswc.parent.value_counts()
    n_child = n_child[n_child.index.isin(tswc.index)]
    tswc.loc[n_child.index, 'degree'] = tswc.loc[n_child.index, 'degree'] + n_child
    return tswc

def get_rid(swc):
    '''
    Find root node.
    '''
    rnode=swc[((swc['parent']<0) & (swc['type']<=1))]
    if rnode.shape[0]<1:
        return -1
    return rnode.index[0]

def get_keypoint(swc, rid=None):  # keypoint: degree ≠ 2 (branches & tips)
    if rid is None:
        rid = get_rid(swc)
    # print(swc.shape)
    swc=get_degree(swc)
    idlist = swc[((swc.degree!=2) | (swc.index==rid))].index.tolist()
    return idlist

def swc2branches(swc):
    '''
    reture branch list of a swc
    '''
    keyids=get_keypoint(swc)
    branches=[]
    for key in keyids:
        if (swc.loc[key,'parent']<0) | (swc.loc[key,'type']<=1):
            continue
        branch=[]
        branch.append(key)
        pkey=swc.loc[key,'parent']
        while True:
            branch.append(pkey)
            if pkey in keyids:
                break
            key=pkey
            pkey=swc.loc[key,'parent']
        branches.append(branch)
    return branches

class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Initial Settings')
        layout = QVBoxLayout()
        
        # Screen size
        self.widthInput = QLineEdit('1920')    # 512, 288
        self.heightInput = QLineEdit('1080')
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(QLabel('Screen Width:'))
        hLayout1.addWidget(self.widthInput)
        hLayout1.addWidget(QLabel('Screen Height:'))
        hLayout1.addWidget(self.heightInput)
        layout.addLayout(hLayout1)
        
        # Window start position
        self.xPosInput = QLineEdit('3824')
        self.yPosInput = QLineEdit('-16')  
        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(QLabel('Start X:'))
        hLayout2.addWidget(self.xPosInput)
        hLayout2.addWidget(QLabel('Start Y:'))
        hLayout2.addWidget(self.yPosInput)
        layout.addLayout(hLayout2)
        
        # Submit button
        self.submitButton = QPushButton('Submit')
        self.submitButton.clicked.connect(self.accept)
        layout.addWidget(self.submitButton)
        
        self.setLayout(layout)

    def getValues(self):
        return int(self.widthInput.text()), int(self.heightInput.text()), int(self.xPosInput.text()), int(self.yPosInput.text())

class MyWindow(QWidget):
    def __init__(self):
        '''
        Initialize windows and variables
        '''
        super(MyWindow, self).__init__()
        self.mediaPlayers = []      # Used to store all media players
        self.initSettings()
        self.initUI()

    def initSettings(self):
        # Launch settings dialog and get screen dimensions and start position
        settingsDialog = SettingsDialog()
        result = settingsDialog.exec_()

        if result == QDialog.Accepted:
            self.screen_width, self.screen_height, self.start_x, self.start_y = settingsDialog.getValues()
        else:
            sys.exit(0)       # Exit the app if the dialog was closed or cancelled

    def initUI(self):
        '''
        Initialize user interface
        '''
        self.grid = QGridLayout()    # 创建一个网格布局
        self.setLayout(self.grid)
        self.grid.setSpacing(0)

        # self.screen_width, self.screen_height = 1920, 1080
        # self.screen_width, self.screen_height = 512, 288
        total_width = 5 * self.screen_width
        total_height = 3 * self.screen_height
        # self.setGeometry(3825, -16, total_width, total_height)
        # self.setGeometry(-11, -14, total_width, total_height)
        self.setGeometry(self.start_x, self.start_y, total_width, total_height)

        self.selectDir()

        self.setWindowTitle('Multimedia Viewer')
        # self.setWindowFlags(Qt.FramelessWindowHint)    # 无边框窗口
        self.show()

        # window_frame_height = self.frameGeometry().height() - self.geometry().height()    # 上下边框的总高度：32
        # window_frame_width = self.frameGeometry().width() - self.geometry().width()       # 左右边框的总高度：2
        # print(window_frame_height, window_frame_width) 

    def selectDir(self):
        '''
        Allow users to select a directory and load supported files
        '''
        while True:       # Keep prompting the user until a valid directory is seleceted or user cancels
            # Select a directory
            dir_name = QFileDialog.getExistingDirectory(self, 'Select a directory', '/home')
            
            if not dir_name:
                break     # user cancelled the directory selection
            
            files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
            files.sort(key = lambda x: int(x.split("-")[0]) if x.split("-")[0].isdigit() else float('inf'))
            supported_files = [f for f in files if f.endswith(('.swc', '.eswc', '.mp4', '.avi', '.jpg', '.png'))][:15]

            # Initialize QProgressDialog
            progress = QProgressDialog("Loading files...", "Abort", 0, len(supported_files), self)
            progress.setWindowModality(Qt.WindowModal)

            progress.setMinimumWidth(800)
            progress.setMinimumHeight(300)
            progress.move(500, 500)
            # progress.setMinimumDuration(0)   # Set the delay for the progress dialog to 0 milliseconds
            progress.show()
            QApplication.processEvents()

            if not supported_files:
                progress.close()    # Close progress bar if no supported files

                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("No supported files found in the selected directory.")
                msg.setWindowTitle("Information")
                ret = msg.exec_()
                if ret == QMessageBox.Ok:
                    continue        # Let the loop prompt the user again

            else:
                positions = [(i, j) for i in range(3) for j in range(5)]
                for idx, file in enumerate(supported_files):
                    file_path = os.path.join(dir_name, file)
                    print(file_path)
                    pos = positions[idx]
                    if file.endswith(('.mp4', '.avi')):
                        self.showVideo(file_path, pos)
                    elif file.endswith(('.jpg', '.png')):
                        self.showImage(file_path, pos)
                    elif file.endswith(('.swc', '.eswc')):
                        self.showSWC(file_path, pos)
                    
                    # Update progress bar
                    progress.setValue(idx + 1)
                    if progress.wasCanceled():
                        break

                # Close progress bar when done
                progress.close()    
                break       # Exit the loop once files are loaded

    def showVideo(self, fname, pos):
        mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayers.append(mediaPlayer)     # Add each new created media player to the list
        videoWidget = QVideoWidget()
        videoWidget.setFixedSize(self.screen_width, self.screen_height)
        self.grid.addWidget(videoWidget, *pos)
        mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fname)))
        mediaPlayer.setVideoOutput(videoWidget)
        mediaPlayer.setPlaybackRate(0.75)         # Set to 0.75 times speed
        mediaPlayer.play()
        mediaPlayer.stateChanged.connect(lambda state: self.mediaStateChanged(state, mediaPlayer))   # Video looping

    def mediaStateChanged(self, state, mediaPlayer):
        '''
        Process media status changes
        '''
        # if state == QMediaPlayer.StoppedState:
        if state == QMediaPlayer.StoppedState and mediaPlayer in self.mediaPlayers:     # Only restart playback when the user manually stops the video
            mediaPlayer.setPosition(0)
            mediaPlayer.play()

    def showImage(self, fname, pos):
        pixmap = QPixmap(fname)
        label = QLabel()
        label.setPixmap(pixmap.scaled(self.screen_width, self.screen_height, Qt.KeepAspectRatio))
        label.setFixedSize(self.screen_width, self.screen_height)
        label.setScaledContents(True)    # Ensure the image always fills the QLabel
        self.grid.addWidget(label, *pos)

    def showSWC(self, fname, pos):
        fig = plt.figure(figsize=(self.screen_width/80, self.screen_height/80))
        ax = fig.add_subplot(111, projection='3d')
        # ax.set_facecolor('black')
        # fig.patch.set_facecolor('black')

        swc = readSWC(fname, mode='simple')
        swc_brs = swc2branches(swc)
        colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
        for br in swc_brs:
            br_color = colors[int(swc.loc[br[0], 'type'])]
            br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
            Xe = br_coords['x'].to_list()
            Ye = br_coords['y'].to_list()
            Ze = br_coords['z'].to_list()
            ax.plot3D(Xe, Ye, Ze, color=br_color, linewidth=1)
        ax.axis('off')
        ax.grid(False)
        # ax.set_xlabel('x')
        # ax.set_ylabel('y')
        # ax.set_zlabel('z')
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(self.screen_width, self.screen_height)
        self.grid.addWidget(canvas, *pos)
        plt.tight_layout()


if __name__ == '__main__':
    app = QApplication(sys.argv + ['--no-sandbox'])
    ex = MyWindow()

    sys.exit(app.exec_())
    



    