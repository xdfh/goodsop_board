import numpy as np
from tflite_runtime.interpreter import Interpreter
import sys
import os

class ASRService:
    def __init__(self, model_path: str, device: str = "cpu"):
        print(f"配置的目标设备是: {device.upper()}")

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

    def transcribe(self, audio_data: np.ndarray) -> str:
        input_index = self.input_details[0]['index']

        # 动态调整输入张量的大小以匹配实际的音频数据。
        # 这是处理可变长度输入的 TFLite 模型的标准做法。
        # 模型加载时可能有一个默认或占位的输入尺寸（例如 1），
        # 在每次推理前，都需要先将输入张量调整为真实数据的尺寸。
        self.interpreter.resize_tensor_input(input_index, audio_data.shape)
        self.interpreter.allocate_tensors()

        self.interpreter.set_tensor(input_index, audio_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        # 模型的输出是字符概率序列，需要进行解码。
        # 在本示例中，我们假设使用简单的 argmax 解码。
        # 实际的实现需要更复杂的 CTC 集束搜索解码器。
        predicted_indices = np.argmax(output_data[0], axis=1)
        
        # 这是一个字符映射的占位符。
        # 您需要根据模型的词汇表，将这些整数索引映射到实际的字符。
        vocabulary = [' ', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', "'"]
        
        # 简单的解码逻辑
        decoded_text = ""
        for index in predicted_indices:
            if index < len(vocabulary):
                decoded_text += vocabulary[index]
        
        # 后处理，以移除 CTC 输出中重复的字符和空格。
        processed_text = ""
        for i, char in enumerate(decoded_text):
            if i == 0 or char != decoded_text[i-1]:
                processed_text += char
        processed_text = processed_text.replace(" ", " ").strip()
        
        return processed_text 