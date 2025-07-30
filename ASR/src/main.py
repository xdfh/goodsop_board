import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from .asr_service import ASRService
import io
import traceback
import time
import logging
from pydub import AudioSegment
from .config import settings  # 导入新的配置对象

# --- 服务生命周期管理 ---
# 使用 lifespan 事件，确保 ASRService 在应用启动时加载，在关闭时清理
asr_service_instance = {"instance": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动时调用的生命周期函数。
    负责初始化 ASR 服务。
    """
    logging.info("--- 应用启动 ---")
    
    # 将整个 settings 对象传递给 ASRService
    app.state.asr_service = ASRService(settings)
    
    logging.info("--- ASR 服务已在 app.state.asr_service 中初始化 ---")
    yield
    logging.info("--- 应用关闭 ---")

# --- 创建 FastAPI 应用实例 ---
# 确保在 lifespan 定义之后创建 app
app = FastAPI(
    title="ASR API",
    description="一个使用 RKNN 模型的语音转文字 API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/api")
async def redirect_to_docs():
    """
    提供一个方便的 /api 路径重定向到 /docs 页面。
    """
    return RedirectResponse(url="/docs")

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    asr_service = asr_service_instance.get("instance")
    if not asr_service:
        raise HTTPException(status_code=503, detail="ASR 服务尚未初始化，请稍后再试。")
    
    start_time = time.time()  # 记录开始时间

    if not file.filename.endswith((".wav", ".mp3", ".flac", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail="文件类型无效，请上传 wav, mp3, flac, m4a, ogg 等常见音频格式。")

    try:
        contents = await file.read()
        
        audio_segment = AudioSegment.from_file(io.BytesIO(contents))
        audio_duration_seconds = len(audio_segment) / 1000.0  # 获取音频时长（秒）
        
        # 步骤 1: 使用 pydub 进行重采样和声道转换，确保格式正确
        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)

        # 步骤 2: 将 pydub 的音频数据转换为 float32 的 numpy 数组
        # pydub 以整数形式提供样本，我们需要将其标准化到 [-1.0, 1.0] 的浮点范围
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        
        # sample_width 为 2 表示 16-bit PCM，其最大值为 32767
        if audio_segment.sample_width == 2:
            audio_data = samples / 32767.0
        else:
            # 为其他位深度提供一个通用标准化（尽管 16-bit 是最常见的）
            audio_data = samples / (2**(audio_segment.sample_width * 8 - 1))

        # 直接调用新的 ASRService 进行端到端处理
        full_transcription = asr_service.transcribe(audio_data)

        end_time = time.time()  # 记录结束时间
        processing_time_seconds = end_time - start_time
        processing_ratio = processing_time_seconds / audio_duration_seconds if audio_duration_seconds > 0 else 0

        return {
            "transcription": full_transcription.strip(),
            "audio_duration_seconds": round(audio_duration_seconds, 2),
            "processing_time_seconds": round(processing_time_seconds, 2),
            "processing_ratio": round(processing_ratio, 2)
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_config=settings.LOGGING_CONFIG
    ) 