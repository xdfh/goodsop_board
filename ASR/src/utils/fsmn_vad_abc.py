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
    def __init__(self, cmvn_file: str, **kwargs) -> None:
        frame_length = kwargs.get("frame_length", 25)
        frame_shift = kwargs.get("frame_shift", 10)
        n_mels = kwargs.get("n_mels", 80)
        fs = kwargs.get("fs", 16000)
        self.lfr_m = kwargs.get("lfr_m", 5) # Default to 5 to get 80 -> 400
        self.lfr_n = kwargs.get("lfr_n", 1)
        
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
        frame, dim = inputs.shape
        means = np.tile(self.cmvn[0:1, :dim], (frame, 1))
        vars = np.tile(self.cmvn[1:2, :dim], (frame, 1))
        return (inputs + means) * vars

    def get_features(self, waveform: np.ndarray) -> np.ndarray:
        fbank = self.fbank(waveform)
        # Re-enable LFR
        lfr_feats = self._apply_lfr(fbank)
        return self._apply_cmvn(lfr_feats)

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
        with open(cmvn_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        means_list, vars_list = [], []
        for i, line in enumerate(lines):
            parts = line.strip().split()
            if not parts:
                continue

            # The actual data is on the line *after* the tag.
            if parts[0] == "<AddShift>":
                if i + 1 < len(lines):
                    # Format is typically: <RealMatrix> N M ... data ... ]
                    means_list = lines[i + 1].split()[3:-1]
            elif parts[0] == "<Rescale>":
                if i + 1 < len(lines):
                    vars_list = lines[i + 1].split()[3:-1]
        
        if not means_list or not vars_list:
            raise ValueError(f"Could not parse means or vars from cmvn file: {cmvn_file}")

        means = np.array(means_list, dtype=np.float64)
        vars = np.array(vars_list, dtype=np.float64)
        return np.array([means, vars])


# Helper class for VAD options
class VADXOptions:
    def __init__(self, **kwargs):
        self.frame_in_ms = kwargs.get("frame_in_ms", 10)
        self.speech_noise_thres = kwargs.get("speech_noise_thres", 0.9)
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
        self.frontend = WavFrontend(cmvn_file=cmvn_path, **self.config.get("WavFrontend", {}).get("frontend_conf", {}))
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

        for i in range(scores.shape[1]):
            speech_prob = scores[0, i, 1] if scores.shape[2] > 1 else (1.0 - scores[0, i, 0])
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