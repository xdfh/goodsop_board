# -*- coding:utf-8 -*-

import logging
import math
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import kaldi_native_fbank as knf
import numpy as np
import yaml
from onnxruntime import (GraphOptimizationLevel, InferenceSession,
                         SessionOptions)
import re


# VAD Onnx Model Runtime
class VadOrtInferRuntimeSession:
    def __init__(self, model_path: str):
        sess_opt = SessionOptions()
        sess_opt.log_severity_level = 4
        sess_opt.enable_cpu_mem_arena = False
        sess_opt.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL

        cpu_ep = "CPUExecutionProvider"
        cpu_provider_options = {"arena_extend_strategy": "kSameAsRequested"}
        providers = [(cpu_ep, cpu_provider_options)]

        self._verify_model(model_path)
        logging.info(f"Loading onnx model at {str(model_path)}")
        self.session = InferenceSession(
            str(model_path), sess_options=sess_opt, providers=providers
        )
        self.input_name = self.session.get_inputs()[0].name

    def __call__(self, input_content: List[np.ndarray]) -> np.ndarray:
        return self.session.run(None, {self.input_name: input_content[0]})

    @staticmethod
    def _verify_model(model_path):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"{model_path} does not exist.")


# Audio Frontend
class WavFrontend:
    def __init__(
        self,
        cmvn_file: str,
        apply_lfr: bool = False, # 新增参数，控制是否应用LFR
        lfr_m: int = 7,
        lfr_n: int = 6,
        **kwargs
    ) -> None:
        frame_length = kwargs.get("frame_length", 25)
        frame_shift = kwargs.get("frame_shift", 10)
        n_mels = kwargs.get("n_mels", 80)
        fs = kwargs.get("fs", 16000)
        
        self.apply_lfr = apply_lfr  # 存储LFR的应用状态
        self.lfr_m = kwargs.get("lfr_m", lfr_m)
        self.lfr_n = kwargs.get("lfr_n", lfr_n)
        
        opts = knf.FbankOptions()
        opts.frame_opts.samp_freq = fs
        opts.frame_opts.dither = kwargs.get("dither", 0.0)
        opts.frame_opts.window_type = kwargs.get("window", "hamming")
        opts.frame_opts.frame_shift_ms = float(frame_shift)
        opts.frame_opts.frame_length_ms = float(frame_length)
        opts.mel_opts.num_bins = n_mels
        self.opts = opts
        self.cmvn = self._load_cmvn(cmvn_file)

    def fbank(self, waveform: np.ndarray) -> np.ndarray:
        waveform = waveform * (1 << 15)
        fbank_fn = knf.OnlineFbank(self.opts)
        fbank_fn.accept_waveform(self.opts.frame_opts.samp_freq, waveform.tolist())
        frames = fbank_fn.num_frames_ready
        mat = np.empty([frames, self.opts.mel_opts.num_bins])
        for i in range(frames):
            mat[i, :] = fbank_fn.get_frame(i)
        return mat.astype(np.float32)

    def _apply_cmvn(self, inputs: np.ndarray) -> np.ndarray:
        means = self.cmvn[0]
        rescales = self.cmvn[1]
        input_dim = inputs.shape[-1]
        
        # 如果CMVN维度与特征维度不匹配，则进行截断或填充，并记录警告
        if means.shape[0] != input_dim:
            logging.warning(
                f"CMVN dimension ({means.shape[0]}) does not match feature dimension ({input_dim}). "
                f"Adjusting CMVN to match feature dimension. This may impact performance."
            )
            
            # 如果CMVN维度更大，则截断
            if means.shape[0] > input_dim:
                means = means[:input_dim]
                rescales = rescales[:input_dim]
            # 如果CMVN维度更小，则用0填充 (不太可能发生，但为了稳健)
            else:
                pad_width = input_dim - means.shape[0]
                # 均值用0填充，尺度用1填充（即不缩放）
                means = np.pad(means, (0, pad_width), 'constant', constant_values=0)
                rescales = np.pad(rescales, (0, pad_width), 'constant', constant_values=1)
                
        return (inputs - means) * rescales

    def get_features(self, waveform: np.ndarray) -> np.ndarray:
        fbank = self.fbank(waveform)
        # 根据 apply_lfr 标志决定是否应用LFR
        if self.apply_lfr:
            lfr_feats = self._apply_lfr(fbank)
            return self._apply_cmvn(lfr_feats)
        else:
            return self._apply_cmvn(fbank)

    def _apply_lfr(self, inputs: np.ndarray) -> np.ndarray:
        T, D = inputs.shape
        T_lfr = (T + self.lfr_n - 1) // self.lfr_n
        
        LFR_inputs = np.zeros((T_lfr, D * self.lfr_m), dtype=np.float32)

        for i in range(T_lfr):
            start = i * self.lfr_n
            end = start + self.lfr_m
            
            # Pad frames if necessary
            current_frames = inputs[start:end, :]
            num_frames, num_dims = current_frames.shape
            
            if num_frames < self.lfr_m:
                padding = np.zeros((self.lfr_m - num_frames, num_dims), dtype=np.float32)
                current_frames = np.vstack((current_frames, padding))

            LFR_inputs[i, :] = current_frames.flatten()
            
        return LFR_inputs

    @staticmethod
    def _load_cmvn(cmvn_file: str) -> np.ndarray:
        """
        Loads CMVN stats from a file. It can handle multiple Kaldi formats:
        1. Nnet1 text format (e.g., am.mvn) without XML-style closing tags.
        2. XML-style text format with closing tags.
        3. Plain text format with two rows of space-separated numbers.
        """
        with open(cmvn_file, 'r', encoding='utf-8') as f:
            content = f.read()

        add_shift_values = None
        rescale_values = None

        # Try parsing Kaldi Nnet1 format (e.g., am.mvn: has <AddShift> but no </AddShift>)
        if '<AddShift>' in content and '</AddShift>' not in content:
            try:
                add_shift_pos = content.find('<AddShift>')
                rescale_pos = content.find('<Rescale>')
                
                if add_shift_pos != -1 and rescale_pos != -1:
                    shift_block = content[add_shift_pos:rescale_pos]
                    rescale_block = content[rescale_pos:]
                    
                    shift_data_match = re.search(r'\[(.*?)\]', shift_block, re.DOTALL)
                    rescale_data_match = re.search(r'\[(.*?)\]', rescale_block, re.DOTALL)

                    if shift_data_match and rescale_data_match:
                        add_shift_values = [float(x) for x in shift_data_match.group(1).strip().split()]
                        rescale_values = [float(x) for x in rescale_data_match.group(1).strip().split()]
            except Exception as e:
                logging.warning(f"Could not parse '{cmvn_file}' as Kaldi Nnet1 format: {e}")
                pass  # Fall through to the next method

        # If Nnet1 parsing failed or wasn't applicable, try XML-style parsing
        if add_shift_values is None:
            if '<AddShift>' in content and '</AddShift>' in content:
                try:
                    shift_block_match = re.search(r'<AddShift>(.*?)</AddShift>', content, re.DOTALL)
                    rescale_block_match = re.search(r'<Rescale>(.*?)</Rescale>', content, re.DOTALL)

                    if shift_block_match and rescale_block_match:
                        shift_data_match = re.search(r'\[(.*?)\]', shift_block_match.group(1), re.DOTALL)
                        rescale_data_match = re.search(r'\[(.*?)\]', rescale_block_match.group(1), re.DOTALL)

                        if shift_data_match and rescale_data_match:
                            add_shift_values = [float(x) for x in shift_data_match.group(1).strip().split()]
                            rescale_values = [float(x) for x in rescale_data_match.group(1).strip().split()]
                except Exception as e:
                    logging.warning(f"Could not parse '{cmvn_file}' as XML-style format: {e}")
                    pass # Fall through
        
        # If both structured formats fail, try plain text
        if add_shift_values is None:
            try:
                lines = content.strip().split('\n')
                data_lines = [line.strip() for line in lines if line.strip().startswith('[')]
                if len(data_lines) >= 2:
                    add_shift_line = data_lines[0].replace('[', '').replace(']', '').strip()
                    add_shift_values = [float(x) for x in add_shift_line.split()]

                    rescale_line = data_lines[1].replace('[', '').replace(']', '').strip()
                    rescale_values = [float(x) for x in rescale_line.split()]
            except Exception as e:
                logging.warning(f"Could not parse '{cmvn_file}' as plain text format: {e}")
                pass

        if add_shift_values is None or rescale_values is None:
            raise ValueError(f"Could not parse CMVN file '{cmvn_file}' with any supported method.")

        # Kaldi's AddShift component contains negative means (-mean).
        means = -np.array(add_shift_values, dtype=np.float32)
        # Kaldi's Rescale component is the scaling factor (1/stddev).
        rescales = np.array(rescale_values, dtype=np.float32)

        if means.ndim != 1 or rescales.ndim != 1 or means.shape != rescales.shape:
            raise ValueError(f"CMVN file parsing error in '{cmvn_file}': Mismatch in loaded stats shapes. Means: {means.shape}, Rescales: {rescales.shape}")

        logging.info(f"Loaded CMVN stats from {cmvn_file} with shape: {means.shape}")
        return np.array([means, rescales])


# Helper class for VAD options
class VADXOptions:
    def __init__(self, **kwargs):
        self.frame_in_ms = kwargs.get("frame_in_ms", 10)
        # Lowered threshold from 0.9, which was too strict, to a more reasonable 0.5
        self.speech_noise_thres = kwargs.get("speech_noise_thres", 0.5)
        self.min_speech_duration_ms = kwargs.get("min_speech_duration_ms", 150)
        self.min_silence_duration_ms = kwargs.get("min_silence_duration_ms", 50)


# Abstract Base Class - defines the interface for VAD models
class FSMNVadABC:
    def __init__(self, model_dir: Path):
        config_path = model_dir / "fsmn-config.yaml"
        if not config_path.is_file():
            raise FileNotFoundError(f"Missing config file: {config_path}")
        with open(config_path, "rb") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        
        model_path = str(model_dir / self.config.get("model_file", "fsmnvad-offline.onnx"))
        self.model = VadOrtInferRuntimeSession(model_path)
        
        self.vad_opts = VADXOptions(**self.config.get("vadPostArgs", {}))

        cmvn_path = str(model_dir / self.config.get("am_mvn_file", "am.mvn"))
        
        frontend_conf = self.config.get("WavFrontend", {}).get("frontend_conf", {})
        
        # 解决TypeError: got multiple values for keyword argument 'lfr_m'
        # 从字典中弹出 lfr 参数，以避免通过 **frontend_conf 重复传递。
        # VAD ONNX模型需要400维输入特征，因此lfr_m应为5。
        lfr_m_val = frontend_conf.pop('lfr_m', 5)
        lfr_n_val = frontend_conf.pop('lfr_n', 1)

        # VAD的WavFrontend需要LFR来输出目标维度特征
        self.frontend = WavFrontend(
            cmvn_file=cmvn_path,
            apply_lfr=True,  # VAD模型强制使用LFR
            lfr_m=lfr_m_val,
            lfr_n=lfr_n_val,
            **frontend_conf
        )
        self.scores = []

    def _extract_feature(self, waveform: np.ndarray) -> np.ndarray:
        return self.frontend.get_features(waveform)

    def _postprocess(self, scores: np.ndarray) -> list:
        # State machine for robust segment detection
        class State(Enum):
            SILENCE = 0
            SPEECH = 1

        segments = []
        state = State.SILENCE
        start_frame = 0
        
        min_speech_frames = self.vad_opts.min_speech_duration_ms // self.vad_opts.frame_in_ms
        min_silence_frames = self.vad_opts.min_silence_duration_ms // self.vad_opts.frame_in_ms
        
        speech_frames_count = 0
        silence_frames_count = 0

        # For debugging VAD performance
        max_speech_prob = 0.0

        for i in range(scores.shape[1]):
            speech_prob = scores[0, i, 1] if scores.shape[2] > 1 else (1.0 - scores[0, i, 0])
            max_speech_prob = max(max_speech_prob, speech_prob)
            is_speech_frame = speech_prob > self.vad_opts.speech_noise_thres

            if state == State.SILENCE:
                if is_speech_frame:
                    speech_frames_count += 1
                    if speech_frames_count >= min_speech_frames:
                        start_frame = i - speech_frames_count + 1
                        state = State.SPEECH
                        silence_frames_count = 0
                else:
                    speech_frames_count = 0 # Reset if speech is not continuous
            
            elif state == State.SPEECH:
                if not is_speech_frame:
                    silence_frames_count += 1
                    if silence_frames_count >= min_silence_frames:
                        end_frame = i - silence_frames_count + 1
                        start_ms = start_frame * self.vad_opts.frame_in_ms
                        end_ms = end_frame * self.vad_opts.frame_in_ms
                        if end_ms > start_ms:
                            segments.append([start_ms, end_ms])
                        state = State.SILENCE
                        speech_frames_count = 0
                else:
                    silence_frames_count = 0 # Reset if silence is not continuous

        # If audio ends while in speech state
        if state == State.SPEECH:
            end_frame = scores.shape[1]
            start_ms = start_frame * self.vad_opts.frame_in_ms
            end_ms = end_frame * self.vad_opts.frame_in_ms
            if end_ms > start_ms:
                segments.append([start_ms, end_ms])
        
        # Log debugging information if no segments are found
        if not segments:
            logging.warning(f"VAD post-processing found no segments. "
                            f"Max speech probability in audio was {max_speech_prob:.4f} "
                            f"(Threshold is {self.vad_opts.speech_noise_thres}).")
                
        return segments
    
    def all_reset_detection(self):
        self.scores = []

# Concrete implementation class, inheriting from the ABC
class FSMNVad(FSMNVadABC):
    def segments_offline(self, waveform: np.ndarray) -> list:
        self.all_reset_detection()
        feats = self._extract_feature(waveform)
        
        feats = feats.astype(np.float32)

        # The model expects a 3D input (batch, time, feats), but feats is 2D.
        # Add a batch dimension using np.expand_dims to make it (1, time, feats).
        feats_batch = np.expand_dims(feats, axis=0)
        scores_list = self.model([feats_batch])
        
        # In offline mode, scores_list should contain a single scores array
        all_scores = scores_list[0] if scores_list else np.array([])
        
        return self._postprocess(all_scores) if all_scores.any() else [] 