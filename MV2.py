from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QFileDialog, QLabel, 
                             QMessageBox, QProgressDialog, QHBoxLayout, QVBoxLayout, 
                             QDialog, QLineEdit, QPushButton)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QTimer, QUrl, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
import matplotlib.pyplot as plt
import pandas as pd
import os
import subprocess

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
        self.widthInput = QLineEdit('3200')
        self.heightInput1 = QLineEdit('2160')
        self.heightInput2 = QLineEdit('1080')
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(QLabel('File Width:'))
        hLayout1.addWidget(self.widthInput)
        hLayout1.addWidget(QLabel('File Height:'))
        hLayout1.addWidget(self.heightInput1)
        hLayout1.addWidget(QLabel('Waiting List Height:'))
        hLayout1.addWidget(self.heightInput2)
        layout.addLayout(hLayout1)
        
        # Window start position
        self.xPosInput = QLineEdit('3830')
        self.yPosInput = QLineEdit('-10')  
        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(QLabel('Start X:'))
        hLayout2.addWidget(self.xPosInput)
        hLayout2.addWidget(QLabel('Start Y:'))
        hLayout2.addWidget(self.yPosInput)
        layout.addLayout(hLayout2)

        # Video playback speed
        self.speedInput = QLineEdit('0.75')
        hLayout3 = QHBoxLayout()
        hLayout3.addWidget(QLabel('Video Playback Speed:'))
        hLayout3.addWidget(self.speedInput)
        layout.addLayout(hLayout3)
        
        # Submit button
        self.submitButton = QPushButton('Submit')
        self.submitButton.clicked.connect(self.accept)
        layout.addWidget(self.submitButton)
        
        self.setLayout(layout)

    def getValues(self):
        return (int(self.widthInput.text()), int(self.heightInput1.text()), 
                int(self.heightInput2.text()), int(self.xPosInput.text()), 
                int(self.yPosInput.text()), float(self.speedInput.text()))

class MyWindow(QWidget):
    def __init__(self):
        print("Initializing MyWindow...")
        super(MyWindow, self).__init__()
        self.mediaPlayers = []         # Used to store all media players
        self.current_index = 0         # The index of the currently displayed file 
        self.swcCache = {}             # A dictionary to store pre-drawn SWC images       
        
        # Set a timer to change the displayed files 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDisplayedFiles)
        print("Timer initialized!")

        self.is_dragging = False      # Used to track whether the window is being dragged
        self.old_pos = None           # Used to store the position where the mouse was pressed

        self.initSettings()
        self.initUI()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.old_pos = event.globalPos()
            
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def initSettings(self):
        # Launch settings dialog and get screen dimensions and start position
        settingsDialog = SettingsDialog()
        result = settingsDialog.exec_()

        if result == QDialog.Accepted:
            self.file_width, self.file_height, self.list_height, self.start_x, self.start_y, self.playback_speed = settingsDialog.getValues()
        else:
            sys.exit(0)       # Exit the app if the dialog was closed or cancelled

    def initUI(self):
        '''
        Initialize user interface
        '''
        self.grid = QGridLayout()      # 创建一个网格布局
        self.setLayout(self.grid)
        self.grid.setSpacing(0)

        total_width = 3 * self.file_width
        total_height = self.file_height + self.list_height
        self.setGeometry(self.start_x, self.start_y, total_width, total_height)

        # Create a horizontal layout to display the list to be displayed
        self.allFilesLayout = QHBoxLayout()
        self.grid.addLayout(self.allFilesLayout, 3, 0, 1, 5)
        self.allFilesLayout.setSpacing(0)

        self.setStyleSheet("MyWindow { background-color: black; }")     # Set background color to black

        self.selectDir()
        self.updateDisplayedFiles()
        self.setWindowTitle('Multimedia Viewer')
        self.show()

    def selectDir(self):
        while True:       # Keep prompting the user until a valid directory is seleceted or user cancels
            self.dir_name = QFileDialog.getExistingDirectory(self, 'Select a directory', '/home')    # Select a directory
            
            if not self.dir_name:
                break     # User cancelled the directory selection
            
            files = [f for f in os.listdir(self.dir_name) if os.path.isfile(os.path.join(self.dir_name, f))]
            files.sort(key = lambda x: int(x.split("-")[0]) if x.split("-")[0].isdigit() else float('inf'))   
            self.supported_files = [f for f in files if f.endswith(('.swc', '.eswc', '.mp4', '.avi', '.jpg', '.png'))][:15]
            print(self.supported_files)

            # Initialize QProgressDialog
            progress = QProgressDialog("Loading files...", "Abort", 0, len(self.supported_files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumWidth(800)
            progress.setMinimumHeight(300)
            progress.move(500, 500)
            progress.show()
            QApplication.processEvents()

            if not self.supported_files:
                # Close progress bar if no supported files
                progress.close()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("No supported files found in the selected directory. Please select another directory.")
                msg.setWindowTitle("Information")
                ret = msg.exec_()
                if ret == QMessageBox.Ok:
                    continue       # Let the loop prompt the user again
            else:
                for i, file in enumerate(self.supported_files):
                    if progress.wasCanceled():
                        break      # Exit the loop if user cliked cancel

                    file_path = os.path.join(self.dir_name, file)
                    iconLabel = QLabel()
                    if file.endswith(('.mp4', '.avi')):
                        thumbnail_path = self.extractVideoThumbnail(file_path)
                        pixmap = QPixmap(thumbnail_path)
                    elif file.endswith(('.jpg', '.png')):
                        pixmap = QPixmap(file_path)
                    elif file.endswith(('.swc', '.eswc')):
                        thumbnail_path = self.generateSWCThumbnail(file_path)
                        pixmap = QPixmap(thumbnail_path)

                        canvas = self.generateSWCCache(file_path)
                        self.swcCache[file_path] = canvas
                    
                    # Check if pixmap is empty
                    if pixmap.isNull():
                        print(f"Error loading image: {file}")
                    else:
                        size = int((3 * self.file_width) / len(self.supported_files))
                        # pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)    # 小图标的大小为100x100
                        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio)   
                        iconLabel.setPixmap(pixmap)
                        iconLabel.setMargin(0)
                        self.allFilesLayout.addWidget(iconLabel) 
                    
                    progress.setValue(i+1)        # Update progress bar
                    QApplication.processEvents()  # Ensure GUI stays responsive

                progress.close()       # Close prpgress bar when done
                break                  # Exit the loop once files are loaded

    def extractVideoThumbnail(self, video_path):
        output_image_path = video_path + ".thumbnail.jpg"
        cmd = ["ffmpeg", "-i", video_path, "-vframes", "1", output_image_path]
        subprocess.run(cmd)
        return output_image_path
    
    def generateSWCThumbnail(self, swc_path):
        output_image_path = swc_path + ".thumbnail.jpg"

        fig = plt.figure(figsize=(self.file_width/80, self.file_height/80))
        ax = fig.add_subplot(111, projection='3d')
        # ax.set_facecolor('black')
        # fig.patch.set_facecolor('black')

        swc = readSWC(swc_path, mode='simple')
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
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=80, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        return output_image_path
    
    # # Create pre-drawn images for each SWC file and store them in swcCache
    # def preloadSWCImages(self):
    #     for file in self.supported_files:
    #         if file.endswith(('.swc', '.eswc')):
    #             file_path = os.path.join(self.dir_name, file)
    #             canvas = self.showSWC(file_path)
    #             self.swcCache[file] = canvas
    
    def updateDisplayedFiles(self):
        self.mediaPlayers = []    # Delete old mediaPlayer

        # # Change the 3 files displayed
        # if self.current_index > len(self.supported_files):
        #     self.current_index = 0
        self.current_index = self.current_index % len(self.supported_files)
        
        if self.supported_files[self.current_index].endswith(('.mp4', '.avi')):
            self.timer.stop()
        else:
            self.timer.start(20000)          # 20 seconds 

        # Remove the currently displayed file
        for i in range(3):
            item = self.grid.itemAtPosition(0, i)
            if item:            # Check if item is not None
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Clear the red border of all small icons
        for j in range(len(self.supported_files)):
            item = self.allFilesLayout.itemAt(j)
            if item:
                iconLabel = item.widget()
                if iconLabel:
                    iconLabel.setStyleSheet("")

        # Show new files
        for i in range(3):
            if self.current_index + i < len(self.supported_files):     # Prevent index from exceeding range
                file = self.supported_files[self.current_index + i]
                file_path = os.path.join(self.dir_name, file)
                pos = (0, i)
                if file.endswith(('.mp4', '.avi')):
                    self.showVideo(file_path, pos)
                elif file.endswith(('.jpg', '.png')):
                    self.showImage(file_path, pos)
                elif file.endswith(('.swc', '.eswc')):
                    self.showSWC(file_path, pos)
                    # canvas = self.swcCache.get(file, None)   # Get the pre-drawn canvas from cache
                    # if canvas:
                    #     self.grid.addWidget(canvas, *pos)     # Add the canvas to the grid

                # Add a red border to the small icons of the three currently displayed files
                item = self.allFilesLayout.itemAt(self.current_index + i)
                if item:
                    iconLabel = item.widget()
                    if iconLabel:
                        iconLabel.setStyleSheet("border: 2px solid Red;")

        self.current_index += 3

    def closeEvent(self, event):
        # Delete all generated thumbnail file when app was closed
        for file in self.supported_files:        
            thumbnail_path = os.path.join(self.dir_name, file + ".thumbnail.jpg")
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        
        super().closeEvent(event)
        
    def showVideo(self, fname, pos):
        mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayers.append(mediaPlayer)     # Add each new created media player to the list
        
        videoWidget = QVideoWidget()
        videoWidget.setFixedSize(self.file_width, self.file_height)
        
        self.grid.addWidget(videoWidget, *pos)

        mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fname)))
        mediaPlayer.setVideoOutput(videoWidget)
        mediaPlayer.setPlaybackRate(self.playback_speed)         # 0.75 times speed
        mediaPlayer.play()
        mediaPlayer.stateChanged.connect(self.mediaStateChanged)  # connect stateChanged signal

        # # 停止并删除旧的mediaPlayer
        # for oldMediaPlayer in self.mediaPlayers:
        #     if oldMediaPlayer != mediaPlayer:
        #         oldMediaPlayer.stop()
        #         # oldMediaPlayer.deleteLater()
        #         QTimer.singleShot(1000, oldMediaPlayer.deleteLater)
        # self.mediaPlayers = []
    
    def mediaStateChanged(self, state):
        '''
        Process media status changes
        '''
        if state == QMediaPlayer.StoppedState:
            if all([mp.state() == QMediaPlayer.StoppedState for mp in self.mediaPlayers]):
                self.updateDisplayedFiles() 

    def showImage(self, fname, pos):
        pixmap = QPixmap(fname)
        label = QLabel()
        label.setPixmap(pixmap.scaled(self.file_width, self.file_height, Qt.KeepAspectRatio))
        label.setFixedSize(self.file_width, self.file_height)
        label.setScaledContents(True)        # Ensure the image always fills the QLabel
        self.grid.addWidget(label, *pos)

    def generateSWCCache(self, swc_path):
        # Draw the SWC files and return a canvas
        fig = plt.figure(figsize=(self.file_width, self.file_height))  # Adjust figure size if necessary
        ax = fig.add_subplot(111, projection='3d')

        swc = readSWC(swc_path, mode='simple')
        swc_brs = swc2branches(swc)
        colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
        for br in swc_brs:
            br_color = colors[int(swc.loc[br[0], 'type'])]
            br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
            Xe = br_coords['x'].to_list()
            Ye = br_coords['y'].to_list()
            Ze = br_coords['z'].to_list()
            ax.plot3D(Xe, Ye, Ze, color=br_color, linewidth=0.5)  # Reduce line width to improve performance
        ax.axis('off')
        ax.grid(False)

        canvas = FigureCanvas(fig)
        # canvas.setFixedSize(self.file_width, self.file_height)
        # plt.tight_layout()
        plt.close(fig)

        return canvas
    
    def showSWC(self, fname, pos):
        canvas = self.swcCache.get(fname)  # Retrieve the pre-generated canvas
        if canvas:
            self.grid.addWidget(canvas, *pos)
        else:
            # Handle the error if the canvas does not exist
            print(f"Error: Canvas for {fname} not found")
    
    # def showSWC(self, fname, pos):
    #     fig = plt.figure(figsize=(self.file_width, self.file_height))
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

    #     canvas = FigureCanvas(fig)
    #     canvas.setFixedSize(self.file_width, self.file_height)
    #     self.grid.addWidget(canvas, *pos)
    #     plt.tight_layout()
    #     plt.close(fig)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWindow()

    sys.exit(app.exec_())



