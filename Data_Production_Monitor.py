import sys
from PyQt5 import QtGui
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea)
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QPieSeries, QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
# import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np
import os

# class CustomQtInteractor(QtInteractor):
#     def keyPressEvent(self, event):
#         # QMainWindow.keyPressEvent(self.parent(), event) # 这里假设MainWindow是QtInteractor的parent。
#         super().keyPressEvent(event)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Neuron Data Reconstruction Monitor")
        self.setGeometry(100, 100, 1200, 800)

        # self.plotter = pv.Plotter()  # 初始化一个 pyvista 绘画对象

        main_layout = QVBoxLayout()

        # 创建一个QFont对象并设置为加粗
        self.boldFont = QFont()
        self.boldFont.setBold(True)

        # 饼图与表格0的水平布局
        title_label_1 = QLabel("Overall Completion Status")
        title_label_1.setFont(self.boldFont)
        title_label_1.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label_1)

        h_layout_1 = QHBoxLayout()                     
        main_layout.addLayout(h_layout_1)

        pie_chart_view = self.create_pie_chart()
        h_layout_1.addWidget(pie_chart_view)

        pie_chart1_view = self.create_pie_chart1()
        h_layout_1.addWidget(pie_chart1_view)

        table0 = self.create_neurons_table()
        h_layout_1.addWidget(table0)

        # 读取GF.csv和3D预览窗口的水平布局
        title_label_2 = QLabel("Preview of Reconstructed Neurons")
        title_label_2.setFont(self.boldFont)
        title_label_2.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label_2)

        h_layout_2 = QHBoxLayout()                     
        main_layout.addLayout(h_layout_2)

        table1 = self.create_df_table()
        h_layout_2.addWidget(table1)

        self.plotter = QtInteractor(self)
        h_layout_2.addWidget(self.plotter)
        
        # 添加柱状图
        title_label_3 = QLabel("Neuron Reconstruction in 2023")
        title_label_3.setFont(self.boldFont)
        title_label_3.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label_3)

        bar_chart_view = self.create_bar_chart()
        main_layout.addWidget(bar_chart_view)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # self.setFocusPolicy(Qt.StrongFocus)  # 设置焦点策略

    # def keyPressEvent(self, event):
    #     print("Key pressed")
    #     if isinstance(self.centralWidget(), QtInteractor):  # 确保当前活动窗口是3D预览窗口
    #         cam = self.plotter.camera
    #         position = list(cam.GetPosition())
    #         focal_point = list(cam.GetFocalPoint())
    #         move_distance = 10.0  # 调整该值来控制移动的距离
            
    #         if event.key() == Qt.Key_Up:
    #             position[1] += move_distance
    #             focal_point[1] += move_distance
    #         elif event.key() == Qt.Key_Down:
    #             position[1] -= move_distance
    #             focal_point[1] -= move_distance
    #         elif event.key() == Qt.Key_Left:
    #             position[0] -= move_distance
    #             focal_point[0] -= move_distance
    #         elif event.key() == Qt.Key_Right:
    #             position[0] += move_distance
    #             focal_point[0] += move_distance
            
    #         cam.SetPosition(position)
    #         cam.SetFocalPoint(focal_point)
            
    #         self.plotter.update()
    #     else:
    #         super().keyPressEvent(event)

    def create_pie_chart(self):
        # 饼图展示
        series = QPieSeries()
        slice1 = series.append("", 104)
        slice2 = series.append("", 14)
        # slice1.setLabel("280 ({:.1f}%)".format(280/352*100))
        # slice2.setLabel("72 ({:.1f}%)".format(72/352*100))
        slice1.setLabel("104 ({:.1f}%)".format(104/118*100))
        slice2.setLabel("14 ({:.1f}%)".format(14/118*100))
        slice1.setLabelVisible(True)
        slice2.setLabelVisible(True)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Rat brain neurons")
        chart.setTitleFont(self.boldFont)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().markers(series)[0].setLabel("Complete")
        chart.legend().markers(series)[1].setLabel('Incomplete')

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view
    
    def create_pie_chart1(self):
        # 饼图展示
        series = QPieSeries()
        slice1 = series.append("", 277)
        slice2 = series.append("", 277)
        slice3 = series.append("", 901)
        slice1.setLabel("277 ({:.1f}%)".format(277/1455*100))
        slice2.setLabel("277 ({:.1f}%)".format(277/1455*100))
        slice3.setLabel("901 ({:.1f}%)".format(901/1455*100))

        slice1.setLabelVisible(True)
        slice2.setLabelVisible(True)
        slice3.setLabelVisible(True)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Human brain neurons")
        chart.setTitleFont(self.boldFont)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().markers(series)[0].setLabel("Completed")
        chart.legend().markers(series)[1].setLabel('First round inspection completed')
        chart.legend().markers(series)[2].setLabel('Incomplete')

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view
    
    def create_neurons_table(self):
        # 24小时内重建的神经元信息表格
        table0 = QTableWidget(7, 3)
        table0.setHorizontalHeaderLabels(["Reconstructed within 24 hours", "Reconstructor ID", "Reviewer ID"])
        
        table0.verticalHeader().setVisible(False)
        table0.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        neurons_data = [
            ("brainID_18865_X_6369.18_Y_3610.07_Z_2974.56.v3dpbd.ano.eswc", "4160  2010  2030", "2010  2030  4160"),
            ("brainID_18865_X_7682_Y_4483.11_Z_2706.72.ano.eswc", "2030  4160", "4160  2030"),
            ("brainID_18866_X_4402.95_Y_5226.23_Z_3723.28.v3dpbd.ano.eswc", "5670  2010  6900  2030", "2030  2010  6900  5670"),
            ("brainID_191798_X_4102.74_Y_5428.85_Z_2298.8.v3dpbd.ano.eswc", "4160  2010", "2010  4160"),
            ("brainID_196466_X_6280.46_Y_11132.7_Z_3818.32.ano.eswc", "5670  6910  4160  2030  2010", "2010"),
            ("brainID_196466_X_6110.26_Y_11301.6_Z_3854.31.ano.eswc", "2000  2010  2030", "2010  2000  2030"),
            ("brainID_18872_X_9632.01_Y_4206.8_Z_854.31.ano.eswc", "5670  2000  6910  2030", "2030  2000  5670  6910")
        ]

        for row, (name, authors, checkers) in enumerate(neurons_data):
            table0.setItem(row, 0, QTableWidgetItem(name))
            table0.setItem(row, 1, QTableWidgetItem(authors))
            table0.setItem(row, 2, QTableWidgetItem(checkers))
        
        return table0

    def create_df_table(self):
        # 读取GF.csv文件并展示
        df = pd.read_csv('GF_test.csv')
        # ['Name', 'Nodes', 'SomaSurface', 'Stems',' Bifurcations', 'Branches', 'Tips',	'OverallWidth', 'OverallHeight','OverallDepth', 
        #  'AverageDiameter', 'Length', 'Surface', 'Volume', 'MaxEuclideanDistance', 'MaxPathDistance', 'MaxBranchOrder', 'AverageContraction', 
        #  'AverageFragmentation', 'AverageParent-daughterRatio', 'AverageBifurcationAngleLocal', 'AverageBifurcationAngleRemote', 'HausdorffDimension']
        columns_to_display = ['Name', 'Nodes', 'SomaSurface', 'Stems', 'OverallWidth']
        df = df[columns_to_display]

        self.table1 = QTableWidget(df.shape[0], df.shape[1])
        self.table1.setHorizontalHeaderLabels(df.columns)
        self.table1.verticalHeader().setVisible(False)
        self.table1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table1.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # 'name'一列显示完整
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                self.table1.setItem(row, col, QTableWidgetItem(str(df.iloc[row,col])))

        self.table1.itemDoubleClicked.connect(self.loadSWC)  # 双击事件

        return self.table1

    def loadSWC(self, item):
        print("loadSWC function called.")
        if item.column() == 0:      # 如果双击的是'name'列
            swc_name = item.text()
            print(swc_name)
            swc_path = "test/" + swc_name

            if not os.path.exists(swc_path):
                print(f"Error: File {swc_path} does not exist!")
                return

            print(f"Loading SWC from {swc_path}")
            swc = readSWC(swc_path, mode='simple')
            swc_brs = swc2branches(swc)
            colors = ['white', 'black', 'red', 'blue', 'magenta', 'green']

            self.plotter.clear()   # 清除当前的3D视图内容

            for br in swc_brs:
                type_idx = int(swc.loc[br[0], 'type'])
                if type_idx < 0 or type_idx >= len(colors):
                    print(f"Invalid type index {type_idx} found!")
                    continue

                br_color = colors[int(swc.loc[br[0], 'type'])]
                br_coords = swc.loc[br, ['x', 'y', 'z']].copy()

                # Ensure data is valid before plotting
                if br_coords.isnull().any().any():
                    print("Null coordinates detected!")
                    continue

                Xe = br_coords['x'].to_list()
                Ye = br_coords['y'].to_list()
                Ze = br_coords['z'].to_list()

                lines = []
                for k in range(len(Xe) - 1):
                    lines.append([Xe[k], Ye[k], Ze[k]])
                    lines.append([Xe[k+1], Ye[k+1], Ze[k+1]])
                
                self.plotter.add_lines(np.array(lines), color=br_color)
                self.plotter.reset_camera()
            
            # self.plotter.show_axes()
            self.plotter.update()    # 更新plotter的显示

    def create_bar_chart(self):
        # 柱状图展示
        set0 = QBarSet('2023')
        set1 = QBarSet('Before 2023')
        set0 << 199 << 414
        set1 << 70 << 0

        # set0.setLabel(str(199))
        # set1.setLabel(str(70))
        # set0.setLabel(str(414))
        # set1.setLabel(str(0))
        
        series = QBarSeries()
        series.append(set0)
        series.append(set1)

        # 每个柱子显示神经元的个数
        # series.setLabelsVisible(True)
        # series.setLabelsFormat("{value}")
        # for barset in series.barSets():
        #     for value in enumerate(barset):
        #         barset.setLabel(str(value))

        # # 每个柱子显示神经元的个数
        # series.setLabelsVisible(True)

        # # 设置柱子的标签
        # set0.setLabels(["199", "414"])
        # set1.setLabels(["70", "0"])

        chart = QChart()
        chart.addSeries(series)
        
        
        chart.setAnimationOptions(QChart.SeriesAnimations)

        categories = ['Rat brain neurons', 'Human brain neurons']
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
                
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


