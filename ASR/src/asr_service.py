# -*- coding:utf-8 -*-

import logging
import time
from pathlib import Path
import numpy as np

# --- 条件导入 NPU 专用模块 ---
# 只有在目标设备 (Linux) 上才能成功导入这些模块
try:
    from .utils.fsmn_vad_abc import FSMNVad, WavFrontend
    from .utils.sense_voice_abc import SenseVoiceInferenceSession
    NPU_MODULES_LOADED = True
except ImportError as e:
    # 此处不再记录日志，因为 logging 尚未安全配置
    # 将在 __init__ 中检查 NPU_MODULES_LOADED 状态并记录
    NPU_MODULES_LOADED = False
    NPU_IMPORT_ERROR = e


class ASRService:
    def __init__(self, model_dir: str, device: str = "cpu"):
        self.device = device.lower()
        self.model_dir = Path(model_dir)
        self.vad_model = None
        self.frontend = None
        self.asr_model = None

        # 在实例化时检查模块加载状态并记录日志
        if not NPU_MODULES_LOADED:
            logging.warning(f"未能加载 NPU 相关模块: {NPU_IMPORT_ERROR}。NPU 功能将在 CPU 模式下被禁用。")

        if self.device == 'npu' and NPU_MODULES_LOADED:
            logging.info("检测到 NPU 模式，正在初始化 SenseVoice RKNN 模型...")
            try:
                logging.info(f"模型目录: {self.model_dir}")
                # 1. 初始化 VAD (语音活动检测) 模型
                logging.info("开始加载 VAD 模型...")
                start_time = time.time()
                self.vad_model = FSMNVad(self.model_dir)
                logging.info(f"VAD 模型加载完成，耗时: {time.time() - start_time:.2f} 秒")

                # 2. 初始化前端特征提取器
                logging.info("开始初始化前端特征提取器...")
                start_time = time.time()
                am_mvn_path = self.model_dir / "am.mvn"
                self.frontend = WavFrontend(cmvn_file=str(am_mvn_path))
                logging.info(f"前端特征提取器初始化完成，耗时: {time.time() - start_time:.2f} 秒")

                # 3. 初始化 SenseVoice RKNN 推理引擎
                logging.info("开始加载 SenseVoice RKNN 模型...")
                start_time = time.time()
                self.asr_model = SenseVoiceInferenceSession(self.model_dir)
                logging.info(f"SenseVoice RKNN 模型加载完成，耗时: {time.time() - start_time:.2f} 秒")
            except Exception as e:
                logging.error(f"在 NPU 模式下初始化 SenseVoice RKNN 模型失败: {e}")
                self.asr_model = None # 确保模型为 None 以防止后续使用

        else:  # CPU 模式 (用于本地开发)
            logging.info("服务在 CPU 模式下运行，ASR 转写功能将被禁用（仅用于开发和测试 API）。")
            self.vad_model = None
            self.frontend = None
            self.asr_model = None

    def transcribe(self, audio_data: np.ndarray) -> str:
        # --- 根据设备类型，选择不同的执行路径 ---
        if self.device == 'npu' and NPU_MODULES_LOADED:
            """
            完整的语音转文字流程。
            1. 使用 VAD 切分有效语音片段。
            2. 对每个片段提取声学特征。
            3. 使用 RKNN 模型进行推理。
            4. 合并所有片段的识别结果。
            """
            logging.info("开始进行语音转文字...")
            start_time = time.time()

            logging.info("步骤 1/3: 正在进行语音活动检测 (VAD)...")
            segments = self.vad_model.segments_offline(audio_data)
            if not segments:
                logging.warning("VAD 未检测到任何有效语音片段。")
                return ""
            logging.info(f"VAD 检测到 {len(segments)} 个语音片段。")

            full_transcription = []
            for i, segment in enumerate(segments):
                start_ms, end_ms = segment
                segment_audio = audio_data[start_ms * 16 : end_ms * 16]
                logging.info(f"步骤 2/3: 正在处理片段 {i+1}/{len(segments)} [{start_ms/1000:.2f}s - {end_ms/1000:.2f}s]...")

                audio_feats = self.frontend.get_features(segment_audio)
                
                logging.info(f"步骤 3/3: 正在对片段 {i+1} 进行 RKNN 推理...")
                asr_result = self.asr_model(audio_feats[None, ...])
                
                logging.info(f"片段 {i+1} 识别结果: '{asr_result}'")
                full_transcription.append(asr_result)

            final_text = " ".join(full_transcription).strip()
            total_time = time.time() - start_time
            logging.info(f"语音转文字完成，总耗时: {total_time:.2f} 秒。")
            logging.info(f"最终识别结果: '{final_text}'")
            
            return final_text
        
        else: # CPU 模式
            logging.warning("在 CPU 模式下调用了转写功能，返回模拟结果。")
            return "（模拟结果）ASR 功能在 CPU 开发模式下不可用，请在 RK3562 设备上进行测试。" 