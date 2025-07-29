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
        
        audio_data, _ = librosa.load(wav_io, sr=16000, mono=True)

        CHUNK_SECONDS = settings.ASR_CHUNK_SECONDS # 使用配置的分块时长
        CHUNK_SAMPLES = 16000 * CHUNK_SECONDS

        full_transcription = ""
        num_samples = len(audio_data)

        # 从 ASR 服务获取模型期望的输入类型
        expected_dtype = asr_service.expected_input_dtype

        if num_samples <= CHUNK_SAMPLES:
            # 根据模型实际需要的类型进行转换
            processed_data = audio_data.astype(expected_dtype)
            
            # 如果是 int8 类型，还需要进行缩放
            if expected_dtype == np.int8:
                processed_data = (processed_data * 127).astype(np.int8)

            audio_data_batched = np.expand_dims(processed_data, axis=0)
            full_transcription = asr_service.transcribe(audio_data_batched)
        else:
            all_transcriptions = []
            print(f"音频过长 ({num_samples / 16000:.2f}秒), 开始分块处理 (每块 {CHUNK_SECONDS} 秒)...")
            
            for i in range(0, num_samples, CHUNK_SAMPLES):
                chunk_end = i + CHUNK_SAMPLES
                chunk = audio_data[i:chunk_end]
                
                print(f"  - 正在处理 {i / 16000:.2f}秒 至 {min(chunk_end / 16000, audio_duration_seconds):.2f}秒...")
                
                # 根据模型实际需要的类型进行转换
                processed_chunk = chunk.astype(expected_dtype)

                # 如果是 int8 类型，还需要进行缩放
                if expected_dtype == np.int8:
                    processed_chunk = (processed_chunk * 127).astype(np.int8)

                chunk_batched = np.expand_dims(processed_chunk, axis=0)
                
                transcription_part = asr_service.transcribe(chunk_batched)
                all_transcriptions.append(transcription_part)
            
            full_transcription = " ".join(all_transcriptions)

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