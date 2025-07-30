# -*- coding:utf-8 -*-

import logging
import math
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import kaldi_native_fbank as knf
import numpy as np
import soundfile as sf
import yaml
from onnxruntime import (GraphOptimizationLevel, InferenceSession,
                         SessionOptions, get_available_providers, get_device)


# VAD Onnx Model Runtime
class VadOrtInferRuntimeSession:
    def __init__(self, model_path: str):
        sess_opt = SessionOptions()
        sess_opt.log_severity_level = 4
        sess_opt.enable_cpu_mem_arena = False
        sess_opt.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL

        cpu_ep = "CPUExecutionProvider"
        cpu_provider_options = {
            "arena_extend_strategy": "kSameAsRequested",
        }
        providers = [(cpu_ep, cpu_provider_options)]

        self._verify_model(model_path)
        logging.info(f"Loading onnx model at {str(model_path)}")
        self.session = InferenceSession(
            str(model_path), sess_options=sess_opt, providers=providers
        )

    def __call__(self, input_content: List[np.ndarray]) -> np.ndarray:
        input_dict = {
            "speech": input_content[0],
            "in_cache0": input_content[1],
            "in_cache1": input_content[2],
            "in_cache2": input_content[3],
            "in_cache3": input_content[4],
        }
        return self.session.run(None, input_dict)

    @staticmethod
    def _verify_model(model_path):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"{model_path} does not exists.")


# Audio Frontend
class WavFrontend:
    def __init__(
        self,
        cmvn_file: str,
        fs: int = 16000,
        window: str = "hamming",
        n_mels: int = 80,
        frame_length: int = 25,
        frame_shift: int = 10,
        lfr_m: int = 7,
        lfr_n: int = 6,
        dither: float = 0,
    ) -> None:
        opts = knf.FbankOptions()
        opts.frame_opts.samp_freq = fs
        opts.frame_opts.dither = dither
        opts.frame_opts.window_type = window
        opts.frame_opts.frame_shift_ms = float(frame_shift)
        opts.frame_opts.frame_length_ms = float(frame_length)
        opts.mel_opts.num_bins = n_mels
        self.opts = opts
        self.lfr_m = lfr_m
        self.lfr_n = lfr_n
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

    def lfr_cmvn(self, feat: np.ndarray) -> np.ndarray:
        feat = self._apply_lfr(feat, self.lfr_m, self.lfr_n)
        feat = self._apply_cmvn(feat)
        return feat

    def get_features(self, waveform: np.ndarray) -> np.ndarray:
        fbank = self.fbank(waveform)
        feats = self.lfr_cmvn(fbank)
        return feats

    @staticmethod
    def _apply_lfr(inputs: np.ndarray, lfr_m: int, lfr_n: int) -> np.ndarray:
        T = inputs.shape[0]
        T_lfr = int(np.ceil(T / lfr_n))
        left_padding = np.tile(inputs[0], ((lfr_m - 1) // 2, 1))
        inputs = np.vstack((left_padding, inputs))
        T = T + (lfr_m - 1) // 2
        LFR_inputs = []
        for i in range(T_lfr):
            if lfr_m <= T - i * lfr_n:
                LFR_inputs.append(
                    (inputs[i * lfr_n: i * lfr_n + lfr_m]).reshape(1, -1)
                )
            else:
                num_padding = lfr_m - (T - i * lfr_n)
                frame = np.hstack((inputs[i * lfr_n:].reshape(-1), np.tile(inputs[-1], num_padding)))
                LFR_inputs.append(frame)
        return np.vstack(LFR_inputs).astype(np.float32)

    def _apply_cmvn(self, inputs: np.ndarray) -> np.ndarray:
        frame, dim = inputs.shape
        means = np.tile(self.cmvn[0:1, :dim], (frame, 1))
        vars = np.tile(self.cmvn[1:2, :dim], (frame, 1))
        return (inputs + means) * vars

    @staticmethod
    def _load_cmvn(cmvn_file: str) -> np.ndarray:
        with open(cmvn_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        means_list, vars_list = [], []
        for i in range(len(lines)):
            line_item = lines[i].split()
            if line_item[0] == "<AddShift>":
                means_list = list(lines[i + 1].split()[3:-1])
            elif line_item[0] == "<Rescale>":
                vars_list = list(lines[i + 1].split()[3:-1])
        means = np.array(means_list).astype(np.float64)
        vars = np.array(vars_list).astype(np.float64)
        return np.array([means, vars])


# FSMN Vad Model
class FSMNVad(FSMNVadABC):
    """
    Wrapper for offline FSMN-VAD model.
    Inherits from FSMNVadABC to reuse its robust _postprocess method.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reset internal states, although it's an offline model,
        # it's good practice to ensure a clean state for each new file.
        self.all_reset_detection()

    def segments_offline(self, waveform: np.ndarray) -> list:
        """
        Processes a full audio waveform to detect speech segments.
        This is the main entry point for this class.
        """
        # Ensure the model is in a clean state before processing a new waveform.
        self.all_reset_detection()

        # Extract acoustic features from the raw waveform.
        feats, self.vad_opts.frame_sample = self._extract_feature(waveform)
        
        # Perform inference and get the speech segments.
        segments, _ = self.infer_offline(feats, waveform, is_final=True)
        return segments

    def infer_offline(self, feats: np.ndarray, waveform: np.ndarray, is_final: bool = True):
        """
        Performs the core inference and post-processing logic.
        """
        # Ensure input features are float32, as required by the ONNX model.
        feats = feats.astype(np.float32)
        
        # Directly compute scores for the entire feature set.
        self._compute_scores(feats)
        
        # Aggregate all computed scores.
        scores = self._get_all_scores()
        
        # Use the robust post-processing logic from the base class.
        return self._postprocess(scores, waveform, is_final=is_final)

    def _get_all_scores(self) -> np.ndarray:
        """
        Concatenates score chunks into a single array.
        """
        if not self.scores:
            return np.array([])
        return np.concatenate(self.scores, axis=1)

    def _compute_scores(self, feats: np.ndarray):
        """
        Runs the ONNX model with only the required 'feats' input.
        This is the fix for the "Invalid input name: in_cache2" error.
        """
        # The offline model expects a single input 'feats' and returns a single output 'scores'.
        scores, = self.model([feats])
        self.scores.append(scores)

    def _detect_common_frames(self):
        # This method is for streaming mode and is not needed for offline processing.
        pass

    def _detect_last_frames(self):
        # This method is for streaming mode and is not needed for offline processing.
        pass


# FSMN Vad Model
# class FSMNVad:
#     def __init__(self, model_dir: str):
#         config_path = Path(model_dir) / "fsmn-config.yaml"
#         with open(config_path, "rb") as f:
#             self.config = yaml.load(f, Loader=yaml.Loader)
        
#         self.frontend = WavFrontend(
#             cmvn_file=Path(model_dir) / "fsmn-am.mvn",
#             **self.config["WavFrontend"]["frontend_conf"],
#         )
#         model_path = str(Path(model_dir) / "fsmnvad-offline.onnx")
#         self.vad = E2EVadModel(model_path, self.config["vadPostArgs"])

#     def _extract_feature(self, waveform):
#         return self.frontend.get_features(waveform)

#     def segments_offline(self, waveform: np.ndarray):
#         feats = self._extract_feature(waveform)
#         segments_part, _ = self.vad.infer_offline(
#             feats[None, ...], waveform[None, ...], is_final=True
#         )
#         return segments_part[0] if segments_part else []


class E2EVadModel:
    # This class is a simplified Python port of the original C++ implementation.
    # It manages the VAD state machine and processes audio frames to detect speech segments.
    def __init__(self, model_path: str, vad_post_args: Dict[str, Any]):
        self.vad_opts = VADXOptions(**vad_post_args)
        self.windows_detector = WindowDetector(
            self.vad_opts.window_size_ms,
            self.vad_opts.sil_to_speech_time_thres,
            self.vad_opts.speech_to_sil_time_thres,
            self.vad_opts.frame_in_ms,
        )
        self.model = VadOrtInferRuntimeSession(model_path)
        self.all_reset_detection()

    def all_reset_detection(self):
        self.frm_cnt = 0
        self.latest_confirmed_speech_frame = 0
        self.vad_state_machine = VadStateMachine.kVadInStateStartPointNotDetected
        self.confirmed_start_frame = -1
        self.output_data_buf = []
        self.output_data_buf_offset = 0
        self.scores_offset = 0
        self.max_end_sil_frame_cnt_thresh = self.vad_opts.max_end_silence_time - self.vad_opts.speech_to_sil_time_thres
        self.reset_detection()

    def reset_detection(self):
        self.continous_silence_frame_count = 0
        self.confirmed_end_frame = -1
        self.vad_state_machine = VadStateMachine.kVadInStateStartPointNotDetected
        self.windows_detector.reset()

    def _compute_scores(self, feats: np.ndarray):
        # 离线模式下，我们直接传递特征，不需要缓存状态
        scores, = self.model([feats])

        self.scores.append(scores)
        self.time_stamps.append(
            (self.audio_chunk_left_samples / self.sample_rate,
             self.audio_chunk_left_samples / self.sample_rate + self.vad_opts.frame_in_ms / 1000.0)
        )
        self.frm_cnt += scores.shape[1]
        self.scores_offset += self.scores.shape[1]

    def infer_offline(self, feats: np.ndarray, waveform: np.ndarray, is_final: bool = True):
        # 确保输入数据类型为 float32，以匹配 ONNX 模型的要求
        feats = feats.astype(np.float32)
        self.waveform = waveform
        self._compute_scores(feats)
        scores = self._get_all_scores()
        return self._postprocess(scores, waveform, is_final=is_final)

    def _get_all_scores(self):
        # in case of short audio
        if not self.scores:
            return []
        scores = np.concatenate(self.scores, axis=1)
        return scores

    def _postprocess(self, scores: Union[list, np.ndarray], waveform: np.ndarray, is_final: bool=True) -> Tuple[list, list]:
        if isinstance(scores, tuple):
            scores = scores[0]
        if isinstance(scores, list):
            if len(scores) > 0:
                scores = np.concatenate(scores, axis=1)
        return [], []

    def _detect_common_frames(self):
        for i in range(self.vad_opts.nn_eval_block_size - 1, -1, -1):
            frame_state = self._get_frame_state(self.frm_cnt - 1 - i)
            self._detect_one_frame(frame_state, self.frm_cnt - 1 - i, False)

    def _detect_last_frames(self):
        for i in range(self.vad_opts.nn_eval_block_size - 1, -1, -1):
            frame_state = self._get_frame_state(self.frm_cnt - 1 - i)
            self._detect_one_frame(frame_state, self.frm_cnt - 1 - i, i == 0)

    def _get_frame_state(self, t: int) -> 'FrameState':
        sum_score = sum(self.scores[0][t - self.scores_offset][sil_pdf_id] for sil_pdf_id in self.vad_opts.sil_pdf_ids)
        speech_prob = math.log(1.0 - sum_score)
        noise_prob = math.log(sum_score) * self.vad_opts.speech_2_noise_ratio
        
        return FrameState.kFrameStateSpeech if speech_prob >= noise_prob + self.vad_opts.speech_noise_thres else FrameState.kFrameStateSil

    def _detect_one_frame(self, cur_frm_state: 'FrameState', cur_frm_idx: int, is_final_frame: bool):
        state_change = self.windows_detector.detect_one_frame(cur_frm_state, cur_frm_idx)
        
        if state_change == AudioChangeState.kChangeStateSil2Speech:
            if self.vad_state_machine == VadStateMachine.kVadInStateStartPointNotDetected:
                start_frame = max(0, cur_frm_idx - self.windows_detector.get_win_size())
                self._on_voice_start(start_frame)
                self.vad_state_machine = VadStateMachine.kVadInStateInSpeechSegment
        
        elif state_change == AudioChangeState.kChangeStateSpeech2Sil:
            if self.vad_state_machine == VadStateMachine.kVadInStateInSpeechSegment:
                if self.continous_silence_frame_count * self.vad_opts.frame_in_ms >= self.max_end_sil_frame_cnt_thresh:
                    self._on_voice_end(cur_frm_idx, False, is_final_frame)
                    self.vad_state_machine = VadStateMachine.kVadInStateEndPointDetected
        
        elif state_change == AudioChangeState.kChangeStateSil2Sil:
            self.continous_silence_frame_count += 1
            if self.vad_opts.detect_mode == VadDetectMode.kVadSingleUtteranceDetectMode.value and \
               self.continous_silence_frame_count * self.vad_opts.frame_in_ms > self.vad_opts.max_start_silence_time:
                self._on_voice_start(0, True)
                self._on_voice_end(0, True, is_final_frame)
                self.vad_state_machine = VadStateMachine.kVadInStateEndPointDetected
        
        if is_final_frame and self.vad_state_machine == VadStateMachine.kVadInStateInSpeechSegment:
            self._on_voice_end(cur_frm_idx, False, True)
            self.vad_state_machine = VadStateMachine.kVadInStateEndPointDetected
            
        if self.vad_state_machine == VadStateMachine.kVadInStateEndPointDetected and \
           self.vad_opts.detect_mode == VadDetectMode.kVadMutipleUtteranceDetectMode.value:
            self.reset_detection()

    def _on_voice_start(self, start_frame: int, fake_result: bool = False):
        if self.confirmed_start_frame == -1:
            self.confirmed_start_frame = start_frame
            if not fake_result:
                self._pop_data_to_output_buf(start_frame, 1, True, False, False)

    def _on_voice_end(self, end_frame: int, fake_result: bool, is_last_frame: bool):
        if self.confirmed_end_frame == -1:
            self.confirmed_end_frame = end_frame
            if not fake_result:
                self._pop_data_to_output_buf(end_frame, 1, False, True, is_last_frame)

    def _pop_data_to_output_buf(self, start_frm: int, frm_cnt: int, first_frm_is_start_point: bool, last_frm_is_end_point: bool, end_point_is_sent_end: bool):
        if not self.output_data_buf or first_frm_is_start_point:
            self.output_data_buf.append(E2EVadSpeechBufWithDoa())
            self.output_data_buf[-1].start_ms = start_frm * self.vad_opts.frame_in_ms
        
        cur_seg = self.output_data_buf[-1]
        cur_seg.end_ms = (start_frm + frm_cnt) * self.vad_opts.frame_in_ms
        if first_frm_is_start_point: cur_seg.contain_seg_start_point = True
        if last_frm_is_end_point: cur_seg.contain_seg_end_point = True

# Helper classes and enums
class VadStateMachine(Enum):
    kVadInStateStartPointNotDetected = 1
    kVadInStateInSpeechSegment = 2
    kVadInStateEndPointDetected = 3

class FrameState(Enum):
    kFrameStateSpeech = 1
    kFrameStateSil = 0

class AudioChangeState(Enum):
    kChangeStateSpeech2Sil = 1
    kChangeStateSil2Speech = 3

class VadDetectMode(Enum):
    kVadSingleUtteranceDetectMode = 0
    kVadMutipleUtteranceDetectMode = 1

class VADXOptions:
    def __init__(self, **kwargs):
        self.sample_rate = 16000
        self.detect_mode = VadDetectMode.kVadMutipleUtteranceDetectMode.value
        self.max_end_silence_time = 800
        self.max_start_silence_time = 3000
        self.window_size_ms = 200
        self.sil_to_speech_time_thres = 150
        self.speech_to_sil_time_thres = 150
        self.speech_2_noise_ratio = 1.0
        self.nn_eval_block_size = 8
        self.speech_noise_thres = 0.6
        self.sil_pdf_ids = [0]
        self.frame_in_ms = 10
        self.frame_length_ms = 25
        self.__dict__.update(kwargs)

class E2EVadSpeechBufWithDoa:
    def __init__(self):
        self.start_ms = 0
        self.end_ms = 0
        self.contain_seg_start_point = False
        self.contain_seg_end_point = False

class WindowDetector:
    def __init__(self, window_size_ms: int, sil_to_speech_time: int, speech_to_sil_time: int, frame_size_ms: int):
        self.win_size_frame = int(window_size_ms / frame_size_ms)
        self.sil_to_speech_frmcnt_thres = int(sil_to_speech_time / frame_size_ms)
        self.speech_to_sil_frmcnt_thres = int(speech_to_sil_time / frame_size_ms)
        self.reset()

    def reset(self):
        self.win_sum = 0
        self.win_state = [0] * self.win_size_frame
        self.cur_win_pos = 0
        self.pre_frame_state = FrameState.kFrameStateSil

    def get_win_size(self) -> int:
        return self.win_size_frame

    def detect_one_frame(self, frameState: FrameState, frame_count: int) -> AudioChangeState:
        cur_frame_state_val = 1 if frameState == FrameState.kFrameStateSpeech else 0
        self.win_sum -= self.win_state[self.cur_win_pos]
        self.win_sum += cur_frame_state_val
        self.win_state[self.cur_win_pos] = cur_frame_state_val
        self.cur_win_pos = (self.cur_win_pos + 1) % self.win_size_frame

        if self.pre_frame_state == FrameState.kFrameStateSil and self.win_sum >= self.sil_to_speech_frmcnt_thres:
            self.pre_frame_state = FrameState.kFrameStateSpeech
            return AudioChangeState.kChangeStateSil2Speech
        if self.pre_frame_state == FrameState.kFrameStateSpeech and self.win_sum <= self.speech_to_sil_frmcnt_thres:
            self.pre_frame_state = FrameState.kFrameStateSil
            return AudioChangeState.kChangeStateSpeech2Sil
        return None 