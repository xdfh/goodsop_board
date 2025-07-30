from rknn.api import RKNN

def convert_to_rknn():
    """将 ONNX 模型转换为 RKNN 模型，并进行INT8量化。"""
    print("--- 开始转换 RKNN 模型 ---")
    rknn = RKNN(verbose=True)
    
    # 1. 配置 RKNN
    print("--> 正在配置 RKNN...")
    rknn.config(
        target_platform='rk3562',
        quantized_dtype='asymmetric_quantized-8',
        optimization_level=3
    )
    
    # 2. 加载 ONNX 模型
    print("--> 正在加载 ONNX 模型: firered_encoder.onnx")
    # --- 关键修正：添加 input_size_list 参数 ---
    # 我们告诉 RKNN，两个输入的典型形状分别是什么
    ret = rknn.load_onnx(
        model='./firered_encoder.onnx',
        inputs=['input', 'input_lengths'],
        input_size_list=[[1, 100, 80], [1]]
    )
    if ret != 0:
        print('加载 ONNX 模型失败！')
        rknn.release()
        return

    # 3. 构建 (量化) RKNN 模型
    print("--> 正在构建模型... (此步骤可能需要几分钟)")
    ret = rknn.build(do_quantization=True, dataset='./dataset.txt')
    if ret != 0:
        print('构建模型失败！')
        rknn.release()
        return
        
    # 4. 导出最终的 RKNN 模型
    output_rknn_file = 'firered_encoder_rk3562.rknn'
    print(f"--> 正在导出 RKNN 模型到: {output_rknn_file}")
    ret = rknn.export_rknn(output_rknn_file)
    if ret != 0:
        print('导出 RKNN 模型失败！')
        rknn.release()
        return
        
    print(f"--- RKNN 模型转换成功！最终文件: {output_rknn_file} ---")
    rknn.release()

if __name__ == '__main__':
    convert_to_rknn()