import numpy as np
import torch
from rknnlite.api import RKNNLite
from .ctc_decoder import CTC


class WenetRknnInference:
    """
    一个用于Wenet RKNN编码器模型的推理引擎。
    它在NPU上运行编码器，然后在CPU上进行CTC贪婪解码。
    """
    def __init__(self, model_path: str, dict_path: str):
        # 1. 初始化RKNNLite运行时
        self.rknn = RKNNLite(verbose=True)
        
        print(f"--> [RKNN] 正在加载RKNN模型: {model_path}")
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            raise RuntimeError(f"加载RKNN模型失败，错误代码: {ret}")
        
        print("--> [RKNN] 正在初始化RKNN运行时环境...")
        ret = self.rknn.init_runtime()
        if ret != 0:
            raise RuntimeError(f"初始化RKNN运行时环境失败，错误代码: {ret}")

        # 2. 初始化CPU上的CTC解码器
        print(f"--> [CPU] 正在初始化CTC贪婪解码器，词典: {dict_path}")
        self.ctc = CTC(dict_path)
        print("--> 推理引擎准备就绪。")

    def __call__(self, audio_feats: torch.Tensor) -> str:
        # The input 'audio_feats' is already a numpy array from asr_service.py.
        # Calling .numpy() on a numpy array causes the AttributeError.
        # We just need to ensure it's the correct type if it comes in as a Tensor.
        if isinstance(audio_feats, torch.Tensor):
            feats_np = audio_feats.numpy()
        else:
            feats_np = audio_feats # It's already a numpy array

        # add a batch axis, shape (1, T, D)
        if feats_np.ndim == 2:
            feats_np = feats_np[None, ...]
            
        seq_len = feats_np.shape[1]
        # The second input to the rknn model is the sequence length
        lengths_np = np.array([seq_len]).astype(np.int64)

        # 1. 在NPU上执行编码器推理
        # print(f"--> [NPU] 正在执行RKNN推理，输入形状: {feats_np.shape}")
        outputs = self.rknn.inference(inputs=[feats_np, lengths_np])
        
        # 编码器的输出是返回列表中的第一个元素
        encoder_out = torch.from_numpy(outputs[0])

        # 2. 在CPU上执行解码
        # print("--> [CPU] 正在解码编码器输出...")
        hyps = self.ctc.greedy_search(encoder_out)
        
        # hyps是一个元组列表 (text, confidence)，我们只需要第一个结果的文本
        result_text = hyps[0][0] if hyps else ""
        return result_text