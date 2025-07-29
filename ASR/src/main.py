import librosa
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from .asr_service import ASRService
import io
import traceback
import time
from pydub import AudioSegment
from .config import settings  # 导入新的配置对象

app = FastAPI(
    title="ASR API",
    description=f"一个使用 TFLite 模型的语音转文字 API (设备: {settings.ASR_DEVICE}, 精度: 自动检测)",
    version="1.0.0",
)

@app.get("/api")
async def redirect_to_docs():
    """
    提供一个方便的 /api 路径重定向到 /docs 页面。
    """
    return RedirectResponse(url="/docs")

# 使用新的配置对象初始化服务
# 将配置的设备信息传递给服务
asr_service = ASRService(
    model_dir=settings.MODEL_DIR,
    device=settings.ASR_DEVICE
)

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    start_time = time.time()  # 记录开始时间

    if not (file.filename.endswith(".wav") or file.filename.endswith(".mp3")):
        raise HTTPException(status_code=400, detail="文件类型无效，请上传 .wav 或 .mp3 文件。")

    try:
        contents = await file.read()
        
        audio_segment = AudioSegment.from_file(io.BytesIO(contents))
        audio_duration_seconds = len(audio_segment) / 1000.0  # 获取音频时长（秒）
        
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # 使用 librosa 加载音频为 numpy 数组，确保采样率为 16000 Hz
        audio_data, _ = librosa.load(wav_io, sr=16000, mono=True)

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
    # 使用配置中的 HOST 和 PORT
    uvicorn.run(app, host=settings.HOST, port=settings.PORT) 