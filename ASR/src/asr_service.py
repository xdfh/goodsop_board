import numpy as np
import sys
import os
import json

# 尝试导入轻量级的 tflite_runtime，这在生产/Docker 环境中是首选
try:
    from tflite_runtime.interpreter import Interpreter
    print("INFO: 已成功加载 tflite_runtime.interpreter。")
# 如果失败，则回退到完整的 tensorflow 包，这适用于本地开发环境
except ImportError:
    print("INFO: 未找到 tflite_runtime，回退到 tensorflow.lite.Interpreter。")
    import tensorflow as tf
    # 从完整的 tensorflow 包中获取 Interpreter
    Interpreter = tf.lite.Interpreter


class ASRService:
    def __init__(self, model_dir: str, device: str = "cpu"):
        print(f"配置的目标设备是: {device.upper()}")
        
        self.model_dir = model_dir
        self._load_vocabulary()

        model_path = os.path.join(model_dir, "model.tflite")

        # 在生产环境中，我们只关心 CPU 或 NPU，并直接使用 tflite_runtime
        # 移除了所有对完整 tensorflow 包的依赖和 GPU 代理逻辑
        delegates = None
        
        # 此处可以为将来的 NPU 支持预留逻辑
        if device.lower() == "npu":
            print("警告: NPU 代理逻辑尚未实现，将回退到 CPU。")
            # try:
            #     delegates = [tf.lite.load_delegate('libedgetpu.so.1')]
            # except Exception as e:
            #     delegates = None
            delegates = None

        try:
            # 使用 tflite_runtime 的 Interpreter
            self.interpreter = Interpreter(
                model_path=model_path,
                experimental_delegates=delegates
            )
        except Exception as e:
            print(f"错误: 使用指定代理 ({device}) 初始化解释器失败，将强制使用 CPU。")
            print(f"   - 错误原因: {e}")
            self.interpreter = Interpreter(model_path=model_path)
            
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
    
    def _load_vocabulary(self):
        """从模型目录加载词汇表和特殊标记。"""
        # 加载主词汇表
        vocab_path = os.path.join(self.model_dir, "vocab.json")
        try:
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_dict = json.load(f)
            # 创建从索引到字符的映射
            self.vocab_list = [""] * len(vocab_dict)
            for char, index in vocab_dict.items():
                self.vocab_list[index] = char
        except FileNotFoundError:
            print(f"错误: 在 '{self.model_dir}' 中未找到 vocab.json。将使用默认的英文字母表。")
            self.vocab_list = [' ', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', "'"]

        # 加载并处理特殊标记
        special_tokens_path = os.path.join(self.model_dir, "special_tokens_map.json")
        try:
            with open(special_tokens_path, 'r', encoding='utf-8') as f:
                special_tokens = json.load(f)
            self.unk_token = special_tokens.get("unk_token", "")
            self.pad_token = special_tokens.get("pad_token", "")
        except FileNotFoundError:
            print(f"信息: 在 '{self.model_dir}' 中未找到 special_tokens_map.json。将使用默认值。")
            self.unk_token = ""
            self.pad_token = ""


    @property
    def expected_input_dtype(self):
        """返回模型期望的输入数据类型 (例如, np.float32)"""
        return self.input_details[0]['dtype']

    def transcribe(self, audio_data: np.ndarray) -> str:
        input_index = self.input_details[0]['index']

        # 检查传入的数据类型是否与模型期望的一致
        if audio_data.dtype != self.expected_input_dtype:
            print(f"警告: 传入数据类型 ({audio_data.dtype}) 与模型期望类型 ({self.expected_input_dtype}) 不符。")
            # 这里只打印警告，因为类型转换的逻辑在 main.py 中处理
            # 或者也可以在这里强制转换，但放在调用处更清晰
            # audio_data = audio_data.astype(self.expected_input_dtype)

        # 动态调整输入张量的大小以匹配实际的音频数据。
        # 这是处理可变长度输入的 TFLite 模型的标准做法。
        self.interpreter.resize_tensor_input(input_index, audio_data.shape)
        self.interpreter.allocate_tensors()

        self.interpreter.set_tensor(input_index, audio_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        # 模型的输出是字符概率序列，需要进行解码。
        # 在本示例中，我们假设使用简单的 argmax 解码。
        # 实际的实现需要更复杂的 CTC 集束搜索解码器。
        predicted_indices = np.argmax(output_data[0], axis=1)
        
        # 使用加载的词汇表进行解码
        decoded_text = ""
        for index in predicted_indices:
            if index < len(self.vocab_list):
                decoded_text += self.vocab_list[index]
        
        # CTC 解码后处理
        processed_text = ""
        for i, char in enumerate(decoded_text):
            # 移除连续重复的字符
            if i > 0 and char == decoded_text[i-1]:
                continue
            # 移除填充标记
            if char == self.pad_token:
                continue
            processed_text += char
        
        # 移除可能存在的未知标记（通常是空格或特定符号）
        processed_text = processed_text.replace(self.unk_token, "").strip()
        
        return processed_text 