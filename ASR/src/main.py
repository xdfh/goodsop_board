import io
import time
import traceback
import logging
# from logging.config import dictConfig # 不再需要全局配置

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from contextlib import asynccontextmanager
from pydub import AudioSegment

from .asr_service import ASRService
from .config import settings, LOGGING_CONFIG

# 不再需要在这里应用日志配置
# dictConfig(LOGGING_CONFIG)

# --- 应用启动事件处理器 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动时调用的生命周期函数。
    负责初始化 ASR 服务。
    """
    logging.info("--- 应用启动 ---")
    
    app.state.asr_service = ASRService(settings)
    
    logging.info("--- ASR 服务已在 app.state.asr_service 中初始化 ---")
    yield
    logging.info("--- 应用关闭 ---")

# --- 创建 FastAPI 应用实例 ---
app = FastAPI(
    title="ASR API",
    description="一个使用 RKNN 模型的语音转文字 API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/api")
def read_root():
    return {"message": "Welcome to the ASR API"}

# --- 转写端点 ---
@app.post("/transcribe/")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    """
    接收音频文件，使用 ASR 服务进行转写，并返回结果。
    """
    asr_service = request.app.state.asr_service
    if not asr_service or asr_service.device != 'npu':
        raise HTTPException(status_code=503, detail="ASR 服务尚未初始化或未在NPU模式下运行，请稍后再试。")

    try:
        start_time = time.time()
        contents = await file.read()
        
        audio_segment = AudioSegment.from_file(io.BytesIO(contents))
        audio_duration_seconds = len(audio_segment) / 1000.0

        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)
        
        if audio_segment.sample_width == 2:
            audio_data = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32767.0
        else:
            audio_data = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / (2**(audio_segment.sample_width * 8 - 1))

        full_transcription = asr_service.transcribe(audio_data)

        end_time = time.time()
        processing_time = end_time - start_time

        return {
            "transcription": full_transcription,
            "audio_duration_seconds": round(audio_duration_seconds, 2),
            "processing_time_seconds": round(processing_time, 2),
            "processing_ratio": round(audio_duration_seconds / processing_time, 2) if processing_time > 0 else "inf"
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理音频时发生错误: {str(e)}")

# --- 测试端点 ---
@app.post("/transcribe_test/")
async def transcribe_test(request: Request, file: UploadFile = File(...)):
    """
    一个用于快速测试的端点，返回固定的模拟结果。
    """
    asr_service = request.app.state.asr_service
    if not asr_service:
        raise HTTPException(status_code=503, detail="ASR 服务尚未初始化，请稍后再试。")

    try:
        contents = await file.read()
        audio_segment = AudioSegment.from_file(io.BytesIO(contents))
        audio_duration_seconds = len(audio_segment) / 1000.0

        return {
            "transcription": "这是一个模拟的测试结果。",
            "audio_duration_seconds": round(audio_duration_seconds, 2)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 将日志配置直接传递给 uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True,
        log_config=LOGGING_CONFIG
    ) 