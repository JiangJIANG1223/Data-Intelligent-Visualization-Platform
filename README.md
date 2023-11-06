# Data-Intelligent-Visualization-Platform
**Outline：**
1/ Multimedia viewers to display and render various types of data. 
2/ Neuron data production monitor to provide functionalities such as real-time monitoring and statistics of the data production process, data preview, and assistance in quality control.  

**Multimedia viewers：**

**1/** MV1.py 和 MV2.py分别为 "5×3" 模式① 和 "1×3+WaitingList" 模式② 下的Multimedia Viewer。

**2/** MV1_Animation.py 在模式① 的基础上添加了SWC动画效果的渲染，渲染效果并未达到期望，还在调整中。

![企业微信截图_16992432442689](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/70558573-bfe6-4f1b-9d40-254c38bc0289)

**Neuron data production monitor：**

**1/** Monitor_Information_Extraction.py用于访问服务器，获取需要的统计信息和相关数据及其特征。*****其中在服务器端调用v3d的globa_neuron_feature插件不成功，通过Vaa3D_Plugin_test.py用于单独测试服务器端v3d插件的调用，报错：Error executing Vaa3D command: /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core5Compat.so.6: no version information available (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)/tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core.so.6: version `Qt_6.5' not found (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)。

**2/** Data_Production_Monitor.py根据提取到的信息制作可视化界面，对神经元数据生产过程进行监控和统计。*****因最开始提取的30天未变动的神经元数据情况参差不齐，数据预览总出现问题，所以目前版本使用的是“test”文件夹中先前已经重建完成的数据，对其提取特征保存在“GF_test.csv”文件中，用于“Preview of Reconstructed Neuron”部分的展示。

![企业微信截图_16983299711444](https://github.com/JiangJIANG1223/Data-Intelligent-Visualization-Platform/assets/87358014/eb647843-6ac6-41c8-9ad2-a19ddb0c4f38)

**Other：**

SWC_Multiview.py为SWC的多视角绘制与显示。
