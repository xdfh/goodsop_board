import torch
import yaml
import types
from wenet.utils.init_model import init_model

# 直接从D盘读取模型
MODEL_PATH="/mnt/d/file/asr/FireRedASR/model.pth.tar"

def export_to_onnx():
    print("--- 开始导出 ONNX 模型 ---")
    with open('config.yaml', 'r') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)
    
    args = types.SimpleNamespace()
    args.gpu = -1
    args.checkpoint = None
    args.jit = False

    # 1. 初始化完整的 ASR 模型，以便加载所有权重
    full_model, configs = init_model(args, configs)
    
    print(f"--> 正在加载模型权重: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location='cpu')

    if isinstance(checkpoint, dict) and 'model' in checkpoint:
        state_dict_to_load = checkpoint['model']
    else:
        state_dict_to_load = checkpoint

    full_model.load_state_dict(state_dict_to_load, strict=False)
    full_model.eval()
    print("--> 模型权重加载完成。")

    # --- 关键修正：我们只导出模型中的编码器 (Encoder) 部分 ---
    # 编码器是模型中主要的计算单元，适合在 NPU 上运行
    encoder_model = full_model.encoder
    print("--> 已成功提取 Encoder 用于导出。")

    # 3. 为编码器创建虚拟输入
    input_dim = configs['input_dim']
    batch_size = 1
    sequence_length = 100
    dummy_input = torch.randn(batch_size, sequence_length, input_dim, requires_grad=True)
    dummy_input_lengths = torch.LongTensor([sequence_length])
    
    # 4. 导出编码器为 ONNX
    output_onnx_file = 'firered_encoder.onnx' # 新的文件名
    print(f"--> 正在将 Encoder 导出到: {output_onnx_file}")
    
    # 编码器的 forward 方法接收 (音频特征, 特征长度)
    # 它的输出是 (编码器输出, 编码器掩码)，我们只关心第一个输出
    torch.onnx.export(
        encoder_model, 
        (dummy_input, dummy_input_lengths), 
        output_onnx_file,
        export_params=True, opset_version=12, do_constant_folding=True,
        input_names=['input', 'input_lengths'], 
        output_names=['output'],  # 我们只导出主要的输出张量
        dynamic_axes={'input': {1: 'sequence_length'}, 'output': {1: 'sequence_length'}}
    )
    print(f"--- 编码器 ONNX 模型导出成功！文件名: {output_onnx_file} ---")

if __name__ == '__main__':
    export_to_onnx()