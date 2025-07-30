import numpy as np
import os

# 创建一个目录来存放我们的虚拟特征数据
os.makedirs('calibration_data', exist_ok=True)

# 这个列表将用于存储写入 dataset.txt 的每一行
dataset_lines = []
for i in range(5):
    # --- 关键修正：将序列长度固定为 100 ---
    # 这必须与 convert_to_rknn.py 中 input_size_list 的尺寸保持一致
    seq_len = 100 
    
    # 1. 为第一个输入 ('input') 生成固定长度的特征数据
    feature_data = np.random.rand(1, seq_len, 80).astype(np.float32)
    feature_path = f'calibration_data/sample_feature_{i}.npy'
    np.save(feature_path, feature_data)

    # 2. 为第二个输入 ('input_lengths') 生成对应的长度数据
    length_data = np.array([seq_len]).astype(np.int64)
    length_path = f'calibration_data/sample_length_{i}.npy'
    np.save(length_path, length_data)

    # 3. 将两个文件的路径用空格隔开，作为一行写入列表
    dataset_lines.append(f'{feature_path} {length_path}\n')

# 将正确格式的行写入 dataset.txt
with open('dataset.txt', 'w') as f:
    f.writelines(dataset_lines)
    
print("已成功生成【固定尺寸】的、匹配多输入的虚拟校准数据集。")