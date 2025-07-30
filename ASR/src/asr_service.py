# -*- coding:utf-8 -*-

import logging
import time
from pathlib import Path

import numpy as np
from .config import Settings
from .utils.wenet_rknn_inference import WenetRknnInference
from .utils.fsmn_vad_abc import FSMNVad, WavFrontend


NPU_MODULES_LOADED = True
try:
    from rknnlite.api import RKNNLite
except ImportError:
    NPU_MODULES_LOADED = False
    RKNNLite = None

class ASRService:
    """
    ASR 服务类，负责加载模型并提供语音转文字功能。
    根据配置，可以在 NPU 或 CPU 模式下运行。
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = settings.ASR_DEVICE
        self.asr_model = None
        self.vad_model = None
        self.asr_frontend = None # ASR专用的特征提取器

        if self.device == 'npu':
            if NPU_MODULES_LOADED:
                try:
                    logging.info("检测到 NPU 模式，正在初始化 ASR 服务...")
                    
                    # 1. 初始化 VAD 模型 (它内部有自己的带LFR的WavFrontend)
                    logging.info("正在初始化 VAD 模型...")
                    self.vad_model = FSMNVad(model_dir=Path(settings.VAD_MODEL_DIR))
                    logging.info("VAD 模型初始化完成。")

                    # 2. 初始化 ASR 专用的特征提取器 (WavFrontend)，不使用LFR
                    logging.info("正在初始化 ASR 特征提取器 (无 LFR)...")
                    # 注意：ASR模型的CMVN文件通常与VAD不同，这里我们使用配置中为ASR指定的AM_MVN_FILE
                    self.asr_frontend = WavFrontend(
                        cmvn_file=settings.AM_MVN_FILE,
                        apply_lfr=False  # 关键：ASR模型需要80维特征，所以关闭LFR
                    )
                    logging.info("ASR 特征提取器初始化完成。")

                    # 3. 初始化 RKNN ASR 推理模型
                    logging.info("正在初始化 WenetRknnInference (ASR 推理核心)...")
                    self.asr_model = WenetRknnInference(
                        model_path=settings.RKNN_MODEL_FILE,
                        dict_path=settings.DICT_FILE
                    )
                    logging.info("WenetRknnInference 初始化完成。")

                    logging.info("NPU ASR 服务初始化成功。")
                except Exception as e:
                    logging.error(f"初始化 NPU ASR 服务失败: {e}", exc_info=True)
                    self.device = 'cpu'  # 初始化失败，回退到CPU模式
            else:
                logging.warning("RKNN 模块未加载，NPU将不可用。")
                self.device = 'cpu'

        if self.device == 'cpu':
            logging.info("服务在 CPU 模式下运行，ASR 转写功能将被禁用（仅用于开发和测试 API）。")

    def transcribe(self, audio_data: np.ndarray) -> str:
        if self.device == 'npu' and self.asr_model and self.vad_model and self.asr_frontend:
            logging.info("开始进行语音转文字...")
            start_time = time.time()

            # 步骤 1/3: 使用VAD进行语音活动检测
            # VAD模型内部使用其自带的、应用了LFR的特征提取器
            logging.info("步骤 1/3: 正在进行语音活动检测 (VAD)...")
            segments = self.vad_model.segments_offline(audio_data)
            if not segments:
                logging.warning("VAD 未检测到任何有效语音片段。")
                return ""
            logging.info(f"VAD 检测到 {len(segments)} 个语音片段。")

            full_transcription = []
            # 步骤 2/3: 遍历VAD切分出的每个语音片段
            for i, segment in enumerate(segments):
                start_ms, end_ms = segment
                segment_audio = audio_data[start_ms * 16 : end_ms * 16]
                logging.info(f"步骤 2/3: 正在处理片段 {i+1}/{len(segments)} [{start_ms/1000:.2f}s - {end_ms/1000:.2f}s]...")

                # 使用为ASR模型专设的特征提取器（无LFR），提取80维特征
                audio_feats = self.asr_frontend.get_features(segment_audio)
                
                # 将特征填充或截断到模型所需的固定长度（100帧）
                required_frames = 100  # RKNN模型转换时确定的固定输入帧数
                current_frames = audio_feats.shape[0]
                
                if current_frames < required_frames:
                    # 如果当前帧数小于所需帧数，用0填充（静音）
                    padding_size = required_frames - current_frames
                    padding = np.zeros((padding_size, audio_feats.shape[1]), dtype=audio_feats.dtype)
                    final_feats = np.vstack([audio_feats, padding])
                else:
                    # 如果当前帧数大于所需帧数，则截断
                    final_feats = audio_feats[:required_frames, :]
                
                logging.info(f"特征已调整为固定长度 {final_feats.shape[0]} 帧。")

                # 步骤 3/3: 对处理后的特征进行ASR推理和解码
                logging.info(f"步骤 3/3: 正在对片段 {i+1} 进行 RKNN 推理和解码...")
                asr_result = self.asr_model(final_feats)
                
                logging.info(f"片段 {i+1} 识别结果: '{asr_result}'")
                if asr_result:
                    full_transcription.append(asr_result)

            final_text = " ".join(full_transcription).strip()
            
            total_time = time.time() - start_time
            logging.info(f"语音转文字完成，总耗时: {total_time:.2f} 秒。")
            logging.info(f"最终识别结果: '{final_text}'")
            
            return final_text
        
        else: # CPU 模式
            logging.warning("在 CPU 模式下调用了转写功能，返回模拟结果。")
            return "（模拟结果）ASR 功能在 CPU 开发模式下不可用，请在 RK3562 设备上进行测试。"

async def some_async_function():
    # 这个函数可以用来保持事件循环的运行，如果需要的话
    pass 