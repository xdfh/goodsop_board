# -*- coding:utf-8 -*-

import logging
import time
from pathlib import Path
import numpy as np

# --- 条件导入 NPU 专用模块 ---
# 只有在目标设备 (Linux) 上才能成功导入这些模块
try:
    from .utils.fsmn_vad_abc import FSMNVad, WavFrontend
    # --- 修改: 移除旧的, 导入新的推理引擎 ---
    # from .utils.sense_voice_abc import SenseVoiceInferenceSession
    from .utils.wenet_rknn_inference import WenetRknnInference
    NPU_MODULES_LOADED = True
except ImportError as e:
    # 此处不再记录日志，因为 logging 尚未安全配置
    # 将在 __init__ 中检查 NPU_MODULES_LOADED 状态并记录
    NPU_MODULES_LOADED = False
    NPU_IMPORT_ERROR = e


class ASRService:
    # --- 修改: 构造函数现在接收一个 settings 对象 ---
    def __init__(self, settings):
        self.device = settings.ASR_DEVICE.lower()
        # --- 使用 settings 对象中的配置来构建路径 ---
        self.model_dir = Path(settings.MODEL_DIR)
        self.vad_model_dir = Path(settings.VAD_MODEL_DIR)

        self.vad_model = None
        self.frontend = None
        self.asr_model = None

        # 在实例化时检查模块加载状态并记录日志
        if not NPU_MODULES_LOADED:
            logging.error(f"无法加载 NPU 模块: {NPU_IMPORT_ERROR}。请检查 rknn-toolkit-lite2 是否正确安装，以及 librknnrt.so 是否存在于系统中。")
            logging.warning("服务将在 CPU 模式下运行，ASR 功能被禁用。")

        elif self.device == 'npu':
            logging.info("检测到 NPU 模式，正在初始化 Wenet RKNN 模型...")
            try:
                # 1. 初始化 VAD (语音活动检测) 模型 (使用 VAD 专用目录)
                logging.info(f"VAD 模型目录: {self.vad_model_dir}")
                logging.info("开始加载 VAD 模型...")
                start_time = time.time()
                self.vad_model = FSMNVad(self.vad_model_dir)
                logging.info(f"VAD 模型加载完成，耗时: {time.time() - start_time:.2f} 秒")

                # 2. 初始化前端特征提取器 (使用 VAD 专用目录)
                logging.info("开始初始化前端特征提取器...")
                start_time = time.time()
                am_mvn_path = self.vad_model_dir / settings.AM_MVN_FILE
                self.frontend = WavFrontend(cmvn_file=str(am_mvn_path))
                logging.info(f"前端特征提取器初始化完成，耗时: {time.time() - start_time:.2f} 秒")

                # 3. 初始化我们新的 Wenet RKNN 推理引擎 (使用主模型目录)
                logging.info(f"主模型目录: {self.model_dir}")
                logging.info("开始加载 Wenet RKNN 推理引擎...")
                start_time = time.time()
                
                # 从 settings 中读取文件名来构建路径
                rknn_model_path = self.model_dir / settings.RKNN_MODEL_FILE
                dict_path = self.model_dir / settings.DICT_FILE
                
                # 实例化新的推理类
                self.asr_model = WenetRknnInference(
                    model_path=str(rknn_model_path),
                    dict_path=str(dict_path)
                )
                
                logging.info(f"Wenet RKNN 推理引擎加载完成，耗时: {time.time() - start_time:.2f} 秒")
                
            except Exception as e:
                logging.error(f"在 NPU 模式下初始化 Wenet RKNN 模型失败: {e}", exc_info=True)
                logging.warning("由于初始化失败，服务将降级到 CPU 模式运行，ASR 功能被禁用。")
                self.asr_model = None # 确保模型为 None 以防止后续使用

        else:  # CPU 模式 (用于本地开发)
            logging.info("服务在 CPU 模式下运行，ASR 转写功能将被禁用（仅用于开发和测试 API）。")
            self.vad_model = None
            self.frontend = None
            self.asr_model = None

    def transcribe(self, audio_data: np.ndarray) -> str:
        # --- 根据设备类型，选择不同的执行路径 ---
        if self.device == 'npu' and self.asr_model and NPU_MODULES_LOADED:
            """
            完整的语音转文字流程。
            1. 使用 VAD 切分有效语音片段。
            2. 对每个片段提取声学特征。
            3. 使用 RKNN 模型进行推理并解码。
            4. 合并所有片段的识别结果。
            """
            logging.info("开始进行语音转文字...")
            start_time = time.time()

            # --- 暂时绕过VAD，直接处理整个音频以测试ASR核心功能 ---
            logging.warning("注意：VAD（语音活动检测）步骤当前被绕过，用于调试。")
            
            # 1. 提取整个音频的特征
            audio_feats = self.frontend.get_features(audio_data)
            
            # 2. 将特征填充或截断到模型所需的固定长度
            required_frames = 20  # 之前推断出的固定帧数
            current_frames = audio_feats.shape[0]
            
            if current_frames < required_frames:
                # 用静音(0)填充
                padding_size = required_frames - current_frames
                padding = np.zeros((padding_size, audio_feats.shape[1]), dtype=audio_feats.dtype)
                final_feats = np.vstack([audio_feats, padding])
            else:
                # 截断
                final_feats = audio_feats[:required_frames, :]

            # 3. 进行ASR推理
            logging.info("正在对处理后的音频片段进行 RKNN 推理和解码...")
            asr_result = self.asr_model(final_feats)
            final_text = asr_result.strip()
            
            # --- VAD 原始逻辑（已注释掉） ---
            # logging.info("步骤 1/3: 正在进行语音活动检测 (VAD)...")
            # segments = self.vad_model.segments_offline(audio_data)
            # if not segments:
            #     logging.warning("VAD 未检测到任何有效语音片段。")
            #     return ""
            # logging.info(f"VAD 检测到 {len(segments)} 个语音片段。")
            #
            # full_transcription = []
            # for i, segment in enumerate(segments):
            #     start_ms, end_ms = segment
            #     segment_audio = audio_data[start_ms * 16 : end_ms * 16]
            #     logging.info(f"步骤 2/3: 正在处理片段 {i+1}/{len(segments)} [{start_ms/1000:.2f}s - {end_ms/1000:.2f}s]...")
            #
            #     audio_feats = self.frontend.get_features(segment_audio)
            #     
            #     # --- FIX STARTS HERE: Pad or truncate features for fixed-size RKNN model ---
            #     required_frames = 20  # Deduced from RKNN error: 32000 bytes / 4 bytes/float / 400 dims = 20 frames
            #     current_frames = audio_feats.shape[0]
            #     
            #     if current_frames < required_frames:
            #         # Pad with zeros (silence)
            #         padding_size = required_frames - current_frames
            #         padding = np.zeros((padding_size, audio_feats.shape[1]), dtype=audio_feats.dtype)
            #         audio_feats = np.vstack([audio_feats, padding])
            #     elif current_frames > required_frames:
            #         # Truncate to the required size
            #         audio_feats = audio_feats[:required_frames, :]
            #     # --- FIX ENDS HERE ---
            #
            #     logging.info(f"步骤 3/3: 正在对片段 {i+1} 进行 RKNN 推理和解码...")
            #     # The wenet_rknn_inference class now handles adding the batch dimension.
            #     asr_result = self.asr_model(audio_feats)
            #     
            #     logging.info(f"片段 {i+1} 识别结果: '{asr_result}'")
            #     full_transcription.append(asr_result)
            #
            # final_text = " ".join(full_transcription).strip()
            # --- VAD 原始逻辑结束 ---

            total_time = time.time() - start_time
            logging.info(f"语音转文字完成，总耗时: {total_time:.2f} 秒。")
            logging.info(f"最终识别结果: '{final_text}'")
            
            return final_text
        
        else: # CPU 模式
            logging.warning("在 CPU 模式下调用了转写功能，返回模拟结果。")
            return "（模拟结果）ASR 功能在 CPU 开发模式下不可用，请在 RK3562 设备上进行测试。" 