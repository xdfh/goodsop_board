# -*- coding:utf-8 -*-

import logging
import time
from pathlib import Path

import numpy as np
import sentencepiece as spm
from rknnlite.api.rknn_lite import RKNNLite

RKNN_INPUT_LEN = 171
SPEECH_SCALE = 1 / 2  # fp16 推理的缩放因子

class SenseVoiceInferenceSession:
    def __init__(self, model_dir: str):
        model_dir = Path(model_dir)
        embedding_file = model_dir / "embedding.npy"
        encoder_file = model_dir / "sense-voice-encoder.rknn"
        bpe_model_file = model_dir / "chn_jpn_yue_eng_ko_spectok.bpe.model"

        logging.info(f"Loading embedding from {embedding_file}")
        self.embedding = np.load(embedding_file)
        
        logging.info(f"Loading RKNN model {encoder_file}")
        start = time.time()
        self.encoder = RKNNLite(verbose=False)
        self.encoder.load_rknn(str(encoder_file))
        self.encoder.init_runtime()
        logging.info(f"Loading RKNN model takes {time.time() - start:.2f} seconds")

        self.blank_id = 0
        self.sp = spm.SentencePieceProcessor()
        self.sp.load(str(bpe_model_file))

    def __call__(self, speech: np.ndarray) -> str:
        # 假设 language='auto' (index 0), use_itn=False (index 15)
        language_query = self.embedding[[[0]]]
        text_norm_query = self.embedding[[[15]]]
        
        # 简单起见，我们暂时不处理 event/emotion detection
        event_emo_query = np.zeros((1, 2, speech.shape[2]), dtype=np.float32)

        speech = speech * SPEECH_SCALE
        
        input_content = np.concatenate(
            [
                language_query,
                event_emo_query,
                text_norm_query,
                speech,
            ],
            axis=1,
        ).astype(np.float32)

        # Pad to required length
        if input_content.shape[1] < RKNN_INPUT_LEN:
             input_content = np.pad(input_content, ((0, 0), (0, RKNN_INPUT_LEN - input_content.shape[1]), (0, 0)))

        start_time = time.time()
        encoder_out = self.encoder.inference(inputs=[input_content])[0]
        logging.info(f"Encoder inference time: {time.time() - start_time:.4f} seconds")
        
        hypos = self._unique_consecutive(encoder_out[0].argmax(axis=0))
        text = self.sp.DecodeIds(hypos)
        return text

    def _unique_consecutive(self, arr):
        mask = np.append([True], arr[1:] != arr[:-1])
        out = arr[mask]
        out = out[out != self.blank_id]
        return out.tolist() 