import paramiko
import pandas as pd
import io
import os

# 从服务器读取SWC文件
def readSWC(sftp, swc_path, mode='simple'):  # pandas DataFrame
    n_skip = 0

    #  使用DFTP读取远程文件的内容
    with sftp.file(swc_path, "r") as f:
        lines = (f.read().decode('utf-8')).splitlines()
        for line in lines:
            if line.startswith("#"):
                n_skip += 1
            else:
                break

    content = '\n'.join(lines[n_skip:])
    buffer = io.StringIO(content)

    names = ["##n", "type", "x", "y", "z", "r", "parent", "seg_id", "level", "mode"]
    # names = ["##n", "type", "x", "y", "z", "r", "parent"]
    used_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    if mode == 'simple':
        pass

    df = pd.read_csv(buffer, index_col=0, skiprows=n_skip, sep=" ",
                     usecols=used_cols,
                     names=names
                     )
    return df

def sftp_exists(sftp, path):
    """Check if a path exists on the remote server."""
    try:
        sftp.stat(path)
        return True
    except IOError as e:
        # errno 2 means file not found
        if e.errno == 2:
            return False
        raise


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
sftp = client.open_sftp()

# # 检查每个子目录的读取权限并输出结果
# check_permission_cmd = """
# for dir in /TeraConvertedBrain/data/{17298..201586}/*/*; do
#     if [ -d "$dir" ]; then  # 检查是否是目录
#         if [ -r "$dir" ]; then
#             echo "$dir: Permission granted"
#         else
#             echo "$dir: Permission denied"
#         fi
#     fi
# done
# """

# stdin, stdout, stderr = client.exec_command(check_permission_cmd)
# permission_output = stdout.read().decode().strip()
# print(permission_output)

# cmd = 'ls -R /TeraConvertedBrain/data/'
# stdin, stdout, stderr = client.exec_command(cmd)
# output = stdout.read().decode().strip()
# print(output)

# 执行命令来获取数据数量
# cmd = 'find /TeraConvertedBrain/data/{17298..201586}/*/* -type f -name "*.eswc" | wc -l'
cmd = """
for dir in /TeraConvertedBrain/data/{17298..201586}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc"
    fi
done | wc -l
"""

cmd_24h = """
for dir in /TeraConvertedBrain/data/{17298..201586}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc" -mtime 0
    fi
done
"""
cmd_unchanged = """
for dir in /TeraConvertedBrain/data/{17298..201586}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc" -mtime +30
    fi
done
"""

cmd_mb = """
for dir in /TeraConvertedBrain/data/{00011..02327}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc"
    fi
done | wc -l
"""

cmd_mb_2023 = """
for dir in /TeraConvertedBrain/data/{00011..02327}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc" -newermt 2023-01-01 ! -newermt 2024-01-01
    fi
done | wc -l
"""

cmd_hb = """
for dir in /TeraConvertedBrain/data/{15257..201598}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc"
    fi
done | wc -l
"""

cmd_hb_2023 = """
for dir in /TeraConvertedBrain/data/{15257..201598}; do
    if [ -d "$dir" ]; then
        find "$dir" -type f -name "*.eswc" -newermt 2023-01-01 ! -newermt 2024-01-01
    fi
done | wc -l
"""

stdin, stdout, stderr = client.exec_command(cmd)
data = int(stdout.read().decode().strip())
print(f"Reconstruction neurons (this batch): {data}")

stdin, stdout, stderr = client.exec_command(cmd_24h)
data_24h = stdout.read().decode().strip().split('\n')
print(f"Reconstruction neurons within 24h (this batch): {len(data_24h)}")
for path in data_24h:
    swc = readSWC(sftp, path, mode='simple')
    reconstruction = swc[swc['r']>1000]['r'].drop_duplicates().tolist()
    checker = swc[swc['mode']>1000]['mode'].drop_duplicates().tolist()
    print(path, reconstruction, checker)

stdin, stdout, stderr = client.exec_command(cmd_unchanged)
unchanged = stdout.read().decode().strip().split('\n')
print(f"Reconstruction neurons unchanged within 30 days (this batch): {len(unchanged)}")

# 创建临时目录
temp_folder = "/tmp/eswc_temp_folder"
if sftp_exists(sftp, temp_folder):
    # 删除临时文件夹中的内容
    for file in sftp.listdir(temp_folder):
        sftp.remove(os.path.join(temp_folder, file))
else:
    sftp.mkdir(temp_folder)

# 将一个月内未修改的数据复制到临时文件夹中
for file in unchanged:
    remote_source_path = file
    remote_dest_path = os.path.join(temp_folder, os.path.basename(file)).replace("\\", "/")
    copy_cmd = f"cp {remote_source_path} {remote_dest_path}"
    stdin, stdout, stderr = client.exec_command(copy_cmd)

    error = stderr.read().decode().strip()
    if error:
        print(f"Error copying file: {error}")
    # else:
    #     print(f"File copied succussfully from {remote_source_path} to {remote_dest_path}")

# 调用v3d的globa_neuron_feature插件
v3d = "/tmp/Vaa3D_x.1.1.2_Ubuntu/Vaa3D-x.sh"
output_csv = "/tmp/features.csv"
cmd_v3d = f"{v3d} -x global_neuron_feature -f compute_feature_in_folder -i {temp_folder} -o {output_csv}"
stdin, stdout, stderr = client.exec_command(cmd_v3d)
# print(f"Reconstruction neurons unchanged within 30 days (this batch): {len(unchanged)}")

## 处理csv文件

# 删除临时文件夹中的内容
# for file in sftp.listdir(temp_folder):
#     sftp.remove(os.path.join(temp_folder, file))

stdin, stdout, stderr = client.exec_command(cmd_mb)
mb = int(stdout.read().decode().strip())
print(f"Total mouse brain neurons: {mb}")

stdin, stdout, stderr = client.exec_command(cmd_mb_2023)
mb_2023 = int(stdout.read().decode().strip())
print(f"Mouse brain neurons in 2023: {mb_2023}")

stdin, stdout, stderr = client.exec_command(cmd_hb)
hb = int(stdout.read().decode().strip())
print(f"Total human brain neurons: {hb}")

stdin, stdout, stderr = client.exec_command(cmd_hb_2023)
hb_2023 = int(stdout.read().decode().strip())
print(f"Human brain neurons in 2023: {hb_2023}")

# 关闭连接
client.close()






