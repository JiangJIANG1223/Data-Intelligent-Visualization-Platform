from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QFileDialog, QLabel, QFileDialog, QMessageBox, QProgressDialog, 
                             QMainWindow, QVBoxLayout, QDialog, QSizePolicy, QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QTimer, QUrl, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
import sys
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt5.QtWebEngineWidgets import QWebEngineView

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
        self.widthInput = QLineEdit('512')
        self.heightInput = QLineEdit('288')
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(QLabel('Screen Width:'))
        hLayout1.addWidget(self.widthInput)
        hLayout1.addWidget(QLabel('Screen Height:'))
        hLayout1.addWidget(self.heightInput)
        layout.addLayout(hLayout1)
        
        # Window start position
        self.xPosInput = QLineEdit('0')
        self.yPosInput = QLineEdit('0')
        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(QLabel('Start X:'))
        hLayout2.addWidget(self.xPosInput)
        hLayout2.addWidget(QLabel('Start Y:'))
        hLayout2.addWidget(self.yPosInput)
        layout.addLayout(hLayout2)
        
        # Select directory
        self.dirInput = QLineEdit(self)
        self.dirInput.setReadOnly(True)
        self.selectDirButton = QPushButton('Select Directory', self)
        self.selectDirButton.clicked.connect(self.selectDirectory)
        hLayout3 = QHBoxLayout()
        hLayout3.addWidget(QLabel('Directory:'))
        hLayout3.addWidget(self.dirInput)
        hLayout3.addWidget(self.selectDirButton)
        layout.addLayout(hLayout3)

        # Submit button
        self.submitButton = QPushButton('Submit')
        self.submitButton.clicked.connect(self.accept)
        layout.addWidget(self.submitButton)
        
        self.setLayout(layout)

    def selectDirectory(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Select a directory', '/home')
        if dir_name:
            self.dirInput.setText(dir_name)
           
    def getValues(self):
        return (int(self.widthInput.text()), int(self.heightInput.text()), int(self.xPosInput.text()), int(self.yPosInput.text()), self.dirInput.text())


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
            self.screen_width, self.screen_height, self.start_x, self.start_y, self.dir_name = settingsDialog.getValues()
        else:
            sys.exit(0)   # Exit the app if the dialog was closed or cancelled

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

        if self.dir_name:
            self.loadFiles(self.dir_name)

        self.setWindowTitle('Multimedia Viewer')
        # self.setWindowFlags(Qt.FramelessWindowHint)    # 无边框窗口
        self.show()

        # window_frame_height = self.frameGeometry().height() - self.geometry().height()    # 上下边框的总高度：32
        # window_frame_width = self.frameGeometry().width() - self.geometry().width()       # 左右边框的总高度：2
        # print(window_frame_height, window_frame_width) 

    def loadFiles(self, dir_name):
        '''
        load supported files
        '''
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
            # Close progress bar if no supported files
            progress.close()

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No supported files found in the selected directory.")
            msg.setWindowTitle("Information")

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

    def showVideo(self, fname, pos):
        mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayers.append(mediaPlayer)     # Add each new created media player to the list
        videoWidget = QVideoWidget()
        videoWidget.setFixedSize(self.screen_width, self.screen_height)
        self.grid.addWidget(videoWidget, *pos)
        mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fname)))
        mediaPlayer.setVideoOutput(videoWidget)
        mediaPlayer.setPlaybackRate(0.75)        # Set to 0.75 times speed
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
        swc = readSWC(fname, mode='simple')
        swc_brs = swc2branches(swc)

        # 创建plotly图形
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]])
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']

        for br in swc_brs:
            br_color = colors[int(swc.loc[br[0], 'type'])]
            br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
            Xe = br_coords['x'].to_list()
            Ye = br_coords['y'].to_list()
            Ze = br_coords['z'].to_list()
            trace = go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color=br_color, width=2))
            fig.add_trace(trace)
        
        fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)     # 隐藏坐标轴
        fig.update_layout(showlegend=False)    # 隐藏图例

        # 添加动画效果
        frames = []
        # 旋转360度
        for angle in range(0, 360, 10):
            frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=np.sin(np.radians(angle)), y=np.cos(np.radians(angle)), z=1)))))
            frames.append(frame)
        
        # 添加放大局部细节的帧
        zoom_positions = [(0.5, 0.5, 2), (1, 1, 3), (1.5, 1.5, 4)]  # 这里的值需要根据你的数据来设置
        for zoom_pos in zoom_positions:
            frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=zoom_pos[0], y=zoom_pos[1], z=zoom_pos[2])))))
            frames.append(frame)
            frames.append(frame)  # 添加两次以停留在放大的位置
        
        # 添加回到初始位置的帧
        frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=0, y=0, z=0)))))
        frames.append(frame)
        
        fig.frames = frames

        # 设置动画模式和自动播放
        fig.update_layout(
            scene=dict(
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    eye=dict(x=0, y=-1.5, z=1)
                )
            ),
            updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play', method='animate', args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode='immediate', loop=True)])])],
            # updatemenus=[dict(type='buttons', showactive=False)],
        )
        
        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        web_view = QWebEngineView()
        web_view.setHtml(html)
        web_view.setFixedSize(self.screen_width, self.screen_height)
        self.grid.addWidget(web_view, *pos)

    # def showSWC(self, fname, pos):
    #     swc = readSWC(fname, mode='simple')
    #     swc_brs = swc2branches(swc)

    #     # 创建plotly图形
    #     # fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]], subplot_titles=[fname])
    #     fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]])
    #     # fig.update_layout(scene=dict(bgcolor='black'), paper_bgcolor='black')  # 设置背景颜色
    #     fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
    #     colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']

    #     for br in swc_brs:
    #         br_color = colors[int(swc.loc[br[0], 'type'])]
    #         br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
    #         Xe = br_coords['x'].to_list()
    #         Ye = br_coords['y'].to_list()
    #         Ze = br_coords['z'].to_list()
    #         trace = go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color=br_color, width=3))
    #         fig.add_trace(trace)
        
    #     fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)     # 隐藏坐标轴
    #     fig.update_layout(showlegend=False)    # 隐藏图例

    #     # 添加动画效果
    #     frames = []
    #     for angle in range(0, 360, 10):
    #         frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=np.sin(np.radians(angle)), y=np.cos(np.radians(angle)), z=1)))))
    #         frames.append(frame)
    #     fig.frames = frames

    #     # 设置动画模式和自动播放
    #     fig.update_layout(
    #         scene=dict(
    #             camera=dict(
    #                 up=dict(x=0, y=0, z=1),
    #                 eye=dict(x=0, y=-1.5, z=1)
    #             )
    #         ),
    #         updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play', method='animate', args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode='immediate', loop=True)])])],
            
    #     )
        
    #     html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    #     web_view = QWebEngineView()
    #     web_view.setHtml(html)
    #     web_view.setFixedSize(self.screen_width, self.screen_height)
    #     # web_view.setFixedSize(QSizePolicy.Expanding, QSizePolicy.Expanding)
    #     self.grid.addWidget(web_view, *pos)


# class SettingsDialog(QDialog):
#     def __init__(self):
#         super(SettingsDialog, self).__init__()
#         self.setWindowTitle('Initial Settings')
        
#         layout = QVBoxLayout()
        
#         # Screen size
#         self.widthInput = QLineEdit('512')
#         self.heightInput = QLineEdit('288')
#         hLayout1 = QHBoxLayout()
#         hLayout1.addWidget(QLabel('Screen Width:'))
#         hLayout1.addWidget(self.widthInput)
#         hLayout1.addWidget(QLabel('Screen Height:'))
#         hLayout1.addWidget(self.heightInput)
#         layout.addLayout(hLayout1)
        
#         # Window start position
#         self.xPosInput = QLineEdit('0')
#         self.yPosInput = QLineEdit('0')
#         hLayout2 = QHBoxLayout()
#         hLayout2.addWidget(QLabel('Start X:'))
#         hLayout2.addWidget(self.xPosInput)
#         hLayout2.addWidget(QLabel('Start Y:'))
#         hLayout2.addWidget(self.yPosInput)
#         layout.addLayout(hLayout2)
        
#         # Submit button
#         self.submitButton = QPushButton('Submit')
#         self.submitButton.clicked.connect(self.accept)
#         layout.addWidget(self.submitButton)
        
#         self.setLayout(layout)

#     def getValues(self):
#         return int(self.widthInput.text()), int(self.heightInput.text()), int(self.xPosInput.text()), int(self.yPosInput.text())
    
# class MyWindow(QWidget):
#     def __init__(self):
#         '''
#         Initialize windows and variables
#         '''
#         super(MyWindow, self).__init__()
#         self.mediaPlayers = []      # Used to store all media players
#         self.initSettings()
#         self.initUI()

#     def initSettings(self):
#         # Launch settings dialog and get screen dimensions and start position
#         settingsDialog = SettingsDialog()
#         result = settingsDialog.exec_()

#         if result == QDialog.Accepted:
#             self.screen_width, self.screen_height, self.start_x, self.start_y = settingsDialog.getValues()
#         else:
#             sys.exit(0)   # Exit the app if the dialog was closed or cancelled

#     def initUI(self):
#         '''
#         Initialize user interface
#         '''
#         self.grid = QGridLayout()    # 创建一个网格布局
#         self.setLayout(self.grid)
#         self.grid.setSpacing(0)

#         # self.screen_width, self.screen_height = 1920, 1080
#         # self.screen_width, self.screen_height = 512, 288
#         total_width = 5 * self.screen_width
#         total_height = 3 * self.screen_height
#         # self.setGeometry(3825, -16, total_width, total_height)
#         # self.setGeometry(-11, -14, total_width, total_height)
#         self.setGeometry(self.start_x, self.start_y, total_width, total_height)

#         self.selectDir()

#     def selectDir(self):
#         '''
#         Allow users to select a directory and load supported files
#         '''
#         while True:       # Keep prompting the user until a valid directory is seleceted or user cancels
#             # Select a directory
#             dir_name = QFileDialog.getExistingDirectory(self, 'Select a directory', '/home')
            
#             if not dir_name:
#                 break     # user cancelled the directory selection
            
#             files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]

#             files.sort(key = lambda x: int(x.split("-")[0]) if x.split("-")[0].isdigit() else float('inf'))
#             supported_files = [f for f in files if f.endswith(('.swc', '.eswc', '.mp4', '.avi', '.jpg', '.png'))][:15]

#             # Initialize QProgressDialog
#             progress = QProgressDialog("Loading files...", "Abort", 0, len(supported_files), self)
#             progress.setWindowModality(Qt.WindowModal)

#             progress.setMinimumWidth(800)
#             progress.setMinimumHeight(300)
#             progress.move(500, 500)
#             # progress.setMinimumDuration(0)   # Set the delay for the progress dialog to 0 milliseconds
#             progress.show()
#             QApplication.processEvents()

#             if not supported_files:
#                 # Close progress bar if no supported files
#                 progress.close()

#                 msg = QMessageBox()
#                 msg.setIcon(QMessageBox.Information)
#                 msg.setText("No supported files found in the selected directory.")
#                 msg.setWindowTitle("Information")
#                 ret = msg.exec_()
#                 if ret == QMessageBox.Ok:
#                     continue   # Let the loop prompt the user again

#             else:
#                 positions = [(i, j) for i in range(3) for j in range(5)]
#                 for idx, file in enumerate(supported_files):
#                     file_path = os.path.join(dir_name, file)
#                     print(file_path)
#                     pos = positions[idx]
#                     if file.endswith(('.mp4', '.avi')):
#                         self.showVideo(file_path, pos)
#                     elif file.endswith(('.jpg', '.png')):
#                         self.showImage(file_path, pos)
#                     elif file.endswith(('.swc', '.eswc')):
#                         self.showSWC(file_path, pos)
                    
#                     # Update progress bar
#                     progress.setValue(idx + 1)
#                     if progress.wasCanceled():
#                         break

#                 # Close progress bar when done
#                 progress.close()    
#                 break       # Exit the loop once files are loaded

#         self.setWindowTitle('Multimedia Viewer')
#         # self.setWindowFlags(Qt.FramelessWindowHint)    # 无边框窗口
#         self.show()

#         # window_frame_height = self.frameGeometry().height() - self.geometry().height()    # 上下边框的总高度：32
#         # window_frame_width = self.frameGeometry().width() - self.geometry().width()       # 左右边框的总高度：2
#         # print(window_frame_height, window_frame_width) 

#     def showVideo(self, fname, pos):
#         mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
#         self.mediaPlayers.append(mediaPlayer)     # Add each new created media player to the list
#         videoWidget = QVideoWidget()
#         videoWidget.setFixedSize(self.screen_width, self.screen_height)
#         self.grid.addWidget(videoWidget, *pos)
#         mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fname)))
#         mediaPlayer.setVideoOutput(videoWidget)
#         mediaPlayer.setPlaybackRate(0.75)        # Set to 0.75 times speed
#         mediaPlayer.play()
#         mediaPlayer.stateChanged.connect(lambda state: self.mediaStateChanged(state, mediaPlayer))   # Video looping

#     def mediaStateChanged(self, state, mediaPlayer):
#         '''
#         Process media status changes
#         '''
#         # if state == QMediaPlayer.StoppedState:
#         if state == QMediaPlayer.StoppedState and mediaPlayer in self.mediaPlayers:     # Only restart playback when the user manually stops the video
#             mediaPlayer.setPosition(0)
#             mediaPlayer.play()

#     def showImage(self, fname, pos):
#         pixmap = QPixmap(fname)
#         label = QLabel()
#         label.setPixmap(pixmap.scaled(self.screen_width, self.screen_height, Qt.KeepAspectRatio))
#         label.setFixedSize(self.screen_width, self.screen_height)
#         label.setScaledContents(True)    # Ensure the image always fills the QLabel
#         self.grid.addWidget(label, *pos)

#     def showSWC(self, fname, pos):
#         swc = readSWC(fname, mode='simple')
#         swc_brs = swc2branches(swc)

#         # 创建plotly图形
#         # fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]], subplot_titles=[fname])
#         fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]])
#         # fig.update_layout(scene=dict(bgcolor='black'), paper_bgcolor='black')  # 设置背景颜色
#         colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']

#         for br in swc_brs:
#             br_color = colors[int(swc.loc[br[0], 'type'])]
#             br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
#             Xe = br_coords['x'].to_list()
#             Ye = br_coords['y'].to_list()
#             Ze = br_coords['z'].to_list()
#             trace = go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color=br_color, width=2))
#             fig.add_trace(trace)
        
#         fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)         # 隐藏坐标轴

#         # 添加动画效果
#         frames = []
#         for angle in range(0, 360, 10):
#             frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=np.sin(np.radians(angle)), y=np.cos(np.radians(angle)), z=1)))))
#             frames.append(frame)
#         fig.frames = frames

#         # 设置动画模式和自动播放
#         fig.update_layout(
#             scene=dict(
#                 camera=dict(
#                     up=dict(x=0, y=0, z=1),
#                     eye=dict(x=0, y=-1.5, z=1)
#                 )
#             ),
#             updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play', method='animate', args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode='immediate', loop=True)])])],
            
#         )
        
#         html = fig.to_html(full_html=False, include_plotlyjs='cdn')
#         web_view = QWebEngineView()
#         web_view.setHtml(html)
#         web_view.setFixedSize(self.screen_width, self.screen_height)
#         # web_view.setFixedSize(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.grid.addWidget(web_view, *pos)

    # def showSWC(self, fname, pos):
    #     fig = plt.figure(figsize=(self.screen_width/80, self.screen_height/80))
    #     ax = fig.add_subplot(111, projection='3d')
    #     # ax.set_facecolor('black')
    #     # fig.patch.set_facecolor('black')

    #     swc = readSWC(fname, mode='simple')
    #     swc_brs = swc2branches(swc)
    #     colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
    #     for br in swc_brs:
    #         br_color = colors[int(swc.loc[br[0], 'type'])]
    #         br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
    #         Xe = br_coords['x'].to_list()
    #         Ye = br_coords['y'].to_list()
    #         Ze = br_coords['z'].to_list()
    #         ax.plot3D(Xe, Ye, Ze, color=br_color, linewidth=1)
    #     ax.axis('off')
    #     ax.grid(False)
    #     # ax.set_xlabel('x')
    #     # ax.set_ylabel('y')
    #     # ax.set_zlabel('z')
    #     canvas = FigureCanvas(fig)
    #     canvas.setFixedSize(self.screen_width, self.screen_height)
    #     self.grid.addWidget(canvas, *pos)
    #     plt.tight_layout()

    # def showSWC(self, fname, pos):
    #     swc = readSWC(fname, mode='simple')
    #     swc_brs = swc2branches(swc)

    #     # 创建plotly图形
    #     fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]], subplot_titles=[fname])
    #     fig.update_layout(scene=dict(bgcolor='black'), paper_bgcolor='black')
    #     colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']

    #     for br in swc_brs:
    #         br_color = colors[int(swc.loc[br[0], 'type'])]
    #         br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
    #         Xe = br_coords['x'].to_list()
    #         Ye = br_coords['y'].to_list()
    #         Ze = br_coords['z'].to_list()
    #         trace = go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color=br_color, width=1))
    #         fig.add_trace(trace)

    #     # 隐藏坐标轴
    #     fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)

    #     # 添加动画效果，实现360度旋转，并在旋转过程中放大到局部细节，然后再缩小至原始大小
    #     frames = []

    #     # 定义局部细节的相机参数
    #     details = [
    #         dict(eye=dict(x=2, y=2, z=1), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    #         dict(eye=dict(x=-2, y=-2, z=1), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    #         dict(eye=dict(x=1, y=-2, z=1), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    #     ]

    #     # 放大到第一个局部细节
    #     for i in range(60):
    #         frame = go.Frame(layout=dict(scene=dict(camera=details[0])))
    #         frames.append(frame)

    #     # 旋转360度并逐渐切换到不同的局部细节
    #     for angle in range(0, 360, 2):
    #         detail_index = (angle // 120) % 3  # 每120度切换一次局部细节
    #         frame = go.Frame(layout=dict(scene=dict(camera=dict(
    #             eye=dict(x=np.sin(np.radians(angle)), y=np.cos(np.radians(angle)), z=1),
    #             center=details[detail_index]['center'],
    #             up=details[detail_index]['up'],
    #         ))))
    #         frames.append(frame)

    #     # 缩小回原始大小
    #     for i in range(60):
    #         frame = go.Frame(layout=dict(scene=dict(camera=dict(eye=dict(x=0, y=-1.5, z=1), up=dict(x=0, y=0, z=1)))))
    #         frames.append(frame)

    #     fig.frames = frames

    #     # 设置动画模式和自动播放
    #     fig.update_layout(
    #         scene=dict(
    #             camera=dict(
    #                 up=dict(x=0, y=0, z=1),
    #                 eye=dict(x=0, y=-1.5, z=1)
    #             )
    #         ),
    #         updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play', method='animate', args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode='immediate', loop=True)])])],
    #     )
    
#     html = fig.to_html(full_html=False, include_plotlyjs='cdn')
#     web_view = QWebEngineView()
#     web_view.setHtml(html)
#     web_view.setFixedSize(self.screen_width, self.screen_height)
#     self.grid.addWidget(web_view, *pos)

#     # # 自动播放动画
#     # fig.layout.updatemenus[0].buttons[0].args[1]['frame']['redraw'] = True
#     # fig.layout.updatemenus[0].buttons[0].args[1]['mode'] = 'immediate'
#     # fig.layout.updatemenus[0].buttons[0].args[1]['loop'] = True

#     # # 显示图形
#     # fig.show()

if __name__ == '__main__':
    app = QApplication(sys.argv + ['--no-sandbox'])
    ex = MyWindow()

    sys.exit(app.exec_())


# os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--enable-logging=strderr --v=1'

# app = QApplication(sys.argv + ['--disable-gpu'])
# web = QWebEngineView()
# def load_html():
#     web.setHtml("<h1>Hello World</h1>")
# # QTimer.singleShot(1000, load_html)
# # web.load(QUrl("https://www.baidu.com/"))
# # web.load(QUrl("C:/Users/kaixiang/Desktop/127.0.0.1.html"))
# web.show()
# sys.exit(app.exec_())

