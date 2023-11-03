import paramiko

# 设置服务器的信息
hostname = '114.117.165.134'
port = 22        # 默认SSH端口是22
username = 'shengdianjiang'
password = 'jiang@tcloud'

# 创建SSH客户端
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动添加主机密钥
client.connect(hostname, port, username, password)

# 创建SFTP客户端
# sftp = client.open_sftp()

# 添加执行权限
chmod_cmd = "chmod -R u+x /tmp/Vaa3D_x.1.1.2_Ubuntu"
stdin, stdout, stderr = client.exec_command(chmod_cmd)
error = stderr.read().decode().strip()
if error:
    print(f"Error setting execute permission: {error}")


# 调用Vaa3D插件
v3d = "/tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x.sh"
temp_folder = "/tmp/eswc_temp_folder"
output_csv = "/tmp/features.csv"
# cmd_v3d = f"{v3d} -x global_neuron_feature -f compute_feature_in_folder -i {temp_folder} -o {output_csv}"
cmd_v3d = f"export LD_LIBRARY_PATH=/tmp/Vaa3D_x.1.1.2_Ubuntu:$LD_LIBRARY_PATH && {v3d} -x global_neuron_feature -f compute_feature_in_folder -i {temp_folder} -o {output_csv}"
stdin, stdout, stderr = client.exec_command(cmd_v3d)

output = stdout.read().decode()
error = stderr.read().decode()
if error:
    print(f"Error executing Vaa3D command: {error}")
else:
    print(f"Vaa3D command excuted successfully. Output: {output}")

# 关闭连接
client.close()

# Error executing Vaa3D command: /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core5Compat.so.6: no version information available (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)/tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x: /tmp/Vaa3D_x.1.1.2_Ubuntu/libQt6Core.so.6: version `Qt_6.5' not found (required by /tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x)



