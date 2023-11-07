# Data-Intelligent-Visualization-Platform
**Outline：**
**1/* Multimedia viewers to display and render various types of data. 
**2/** Neuron data production monitor to provide functionalities such as real-time monitoring and statistics of the data production process, data preview, and assistance in quality control.  

**Multimedia viewers：**

**1/** MV1.py 和 MV2.py 分别为 "5×3" 模式① 和 "1×3+WaitingList" 模式② 下的 Multimedia Viewer。两种模式①② 适用于实验室大屏幕的初始界面参数设置（默认值）如图所示。

![企业微信截图_1699364921969](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/73b61919-1b57-40e2-9061-88d3c37e05b1)

![企业微信截图_16993644236889](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/6a9ac1bc-e4ba-485b-92c4-c6bac14d8f15)


**2/** MV1_Animation.py 在模式① 的基础上添加了 SWC 动画效果的渲染，渲染效果并未达到期望，还在调整。

![企业微信截图_16992432442689](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/70558573-bfe6-4f1b-9d40-254c38bc0289)

**Neuron data production monitor：**

**1/** Monitor_Information_Extraction.py 用于访问服务器，获取需要的统计信息和相关数据及其特征，主要包括①整体重建情况（鼠脑神经元、人脑神经元）；②24h内改动过的数据及其重建者和检查者；③重建完成的数据及其特征预览；④2023年对比2023年之前的数据重建数量（鼠脑神经元、人脑神经元）。

*****其中在服务器端调用 v3d 的 globa_neuron_feature 插件不成功，通过 Vaa3D_Plugin_test.py 用于单独测试服务器端v3d插件的调用，报错：Error executing Vaa3D command: /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core5Compat.so.6: no version information available (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)/tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core.so.6: version `Qt_6.5' not found (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)。

**2/** Data_Production_Monitor.py 根据提取到的信息制作可视化界面，对神经元数据生产过程进行监控和统计。

*****因最开始提取的30天未变动的神经元数据情况参差不齐，数据预览总出现问题，所以目前版本使用的是 “test” 文件夹中先前已经重建完成的数据，对其提取特征保存在 “GF_test.csv” 文件中，暂用于 “Preview of Reconstructed Neuron” 部分的展示。

![企业微信截图_16983299711444](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/eb647843-6ac6-41c8-9ad2-a19ddb0c4f38)

**Other：**

SWC_Multiview.py 为 SWC 多视角绘制与显示。

![企业微信截图_1699363403401](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/87edb335-5d02-422d-a285-908cee0c3c32)
