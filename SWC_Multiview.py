import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication, QVBoxLayout
from PyQt5.QtCore import Qt
from pyvistaqt import BackgroundPlotter
# import vtk
# import pyvista

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

def synchronize_cameras(renderers, main_renderer):
    main_cam = main_renderer.camera
    for renderer in renderers:
        if renderer != main_renderer:
            cam = renderer.camera
            cam.position = main_cam.position
            cam.focal_point = main_cam.focal_point
            cam.view_up = main_cam.view_up
            renderer.reset_camera_clipping_range()

class MyWindow(QWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 2560, 1440)
        # self.setGeometry(3840, 0, 3480, 2160)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)

        fname, _ = QFileDialog.getOpenFileName(self, 'Open SWC/ESWC File', '', 'SWC Files (*.swc *.eswc;;All Files (*)')
        if fname:
            plotter = BackgroundPlotter(shape=(2, 2), window_size=(1920, 1080))  # create a BackgroundPlotter with 2*2 subgraph layout and size of 1920*1080
            # plotter = BackgroundPlotter(shape=(2, 2)) 
            plotter.app_window.move(200, 200)
            # plotter.app_window.move(3840, 0)
            plotter.set_background("white")

            self.display_swc(fname, plotter) # 使用选择的SWC文件和plotter来显示内容
            layout.addWidget(plotter)  # 将plotter添加到布局中

        self.setLayout(layout)
        self.show()

    def display_swc(self, fname, plotter):
        swc = readSWC(fname, mode='simple')
        swc_brs = swc2branches(swc)
        colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
        views = [(0, 0, 1), (1, 0, 0), (0, 1, 0), (1, 1, 1)]

        renderers = []
        # actors = []
        
        for i in range(2):
            for j in range(2):
                plotter.subplot(i, j)
                plotter.view_vector(views[2*i + j], viewup=(0, 0, 1))
                renderers.append(plotter.renderer)
                # actor = plotter.add_mesh(pyvista.PolyData(), color='white')
                # actors.append(actor)

        for i in range(2):
            for j in range(2):
                plotter.subplot(i, j)
                for br in swc_brs:
                    br_color = colors[int(swc.loc[br[0], 'type'])]
                    br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
                    Xe = br_coords['x'].to_numpy()
                    Ye = br_coords['y'].to_numpy()
                    Ze = br_coords['z'].to_numpy()
                    
                    lines = []
                    for k in range(len(Xe) - 1):
                        lines.append([Xe[k], Ye[k], Ze[k]])
                        lines.append([Xe[k+1], Ye[k+1], Ze[k+1]])
                    
                    plotter.add_lines(np.array(lines), color=br_color)
                    plotter.reset_camera()
                    # polydata = pyvista.PolyData(np.array(lines))
                    # actor.GetMapper().SetInputData(polydata)
                    # actor.GetProperty().SetColor(br_color)

                plotter.show_axes()
                # plotter.view_vector(views[2*i + j], viewup=(0, 0, 1))
            
        # Add abservers to synchronize cameras
        for renderer in renderers:
            renderer.camera.AddObserver("ModifiedEvent", lambda: synchronize_cameras(renderers, renderer))

    # def display_swc(self, fname, plotter):
    #     swc = readSWC(fname, mode='simple')
    #     swc_brs = swc2branches(swc)
    #     colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
    #     views = [(0, 0, 1), (1, 0, 0), (0, 1, 0), (1, 1, 1)]

    #     # Store the camera settings of each subplot
    #     cameras = []
        
    #     for i in range(2):
    #         for j in range(2):
    #             plotter.subplot(i, j)
    #             for br in swc_brs:
    #                 br_color = colors[int(swc.loc[br[0], 'type'])]
    #                 br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
    #                 Xe = br_coords['x'].to_numpy()
    #                 Ye = br_coords['y'].to_numpy()
    #                 Ze = br_coords['z'].to_numpy()
                    
    #                 lines = []
    #                 for k in range(len(Xe) - 1):
    #                     lines.append([Xe[k], Ye[k], Ze[k]])
    #                     lines.append([Xe[k+1], Ye[k+1], Ze[k+1]])
                    
    #                 plotter.add_lines(np.array(lines), color=br_color)
    #                 plotter.reset_camera()
                
    #             plotter.show_axes()
    #             plotter.view_vector(views[2*i + j], viewup=(0, 0, 1))

    #             # Store the camera settings
    #             cameras.append((plotter.renderer.camera.GetViewUp(),
    #                             plotter.renderer.camera.GetFocalPoint(),
    #                             plotter.renderer.camera.GetPosition()))
                
    #     def update_views(caller, event):
    #         # This function will be called whenever the camera of any subplot changes.
    #         # It will synchronize the camera settings of all subplots.
    #         for i, renderer in enumerate(plotter.renderers):
    #                 renderer.camera.SetViewUp(cameras[i][0])
    #                 renderer.camera.SetFocalPoint(cameras[i][1])
    #                 renderer.camera.SetPosition(cameras[i][2])
    #                 renderer.reset_camera_clipping_range()
    #         # Add an observer to the camera of each subplot
    #         for renderer in plotter.renderers:
    #             renderer.camera.AddObserver("ModifiedEvent", update_views)

    #         plotter.link_views()

'''
    # def display_swc(self, fname, plotter):
    #     swc = readSWC(fname, mode='simple')
    #     swc_brs = swc2branches(swc)
    #     # print(swc_brs)
    #     # colors = [(1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0)]
    #     colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']
    #     # Define 4 different views
    #     views = [(0, 0, 1), (1, 0, 0), (0, 1, 0), (1, 1, 1)]
        
    #     for i in range(2):
    #         for j in range(2):
    #             plotter.subplot(i, j)
    #             for br in swc_brs:
    #                 br_color = colors[int(swc.loc[br[0], 'type'])]
    #                 br_coords = swc.loc[br, ['x', 'y', 'z']].copy()
    #                 Xe = br_coords['x'].to_numpy()
    #                 Ye = br_coords['y'].to_numpy()
    #                 Ze = br_coords['z'].to_numpy()
                    
    #                 lines = []
    #                 for k in range(len(Xe) - 1):
    #                     lines.append([Xe[k], Ye[k], Ze[k]])
    #                     lines.append([Xe[k+1], Ye[k+1], Ze[k+1]])
                    
    #                 plotter.add_lines(np.array(lines), color=br_color)
    #                 plotter.reset_camera()
                
    #             # plotter.show_grid()
    #             plotter.show_axes()
    #             plotter.view_vector(views[2*i + j], viewup=(0, 0, 1))

    #     # Link the views of all subplots
    #     plotter.link_views()
'''

if __name__ == "__main__":
    app = QApplication([])
    window = MyWindow()
    app.exec_()

