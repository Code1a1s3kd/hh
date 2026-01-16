import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube Stream API")

# ====== إعداد الكوكيز من متغيرات البيئة ======
# نقوم بكتابة الكوكيز في ملف عند بدء التشغيل إذا كانت موجودة في الـ Environment Variables
COOKIES_FILE_PATH = "cookies.txt"
COOKIES_CONTENT = os.getenv("COOKIES_CONTENT")

if COOKIES_CONTENT:
    with open(COOKIES_FILE_PATH, "w") as f:
        f.write(COOKIES_CONTENT)
    print("✅ Cookies file created from environment variable.")
else:
    print("⚠️ No COOKIES_CONTENT found. Trying to run without cookies (might fail for some videos).")

# ==========================================

class FormatRequest(BaseModel):
    url: str

class StreamRequest(BaseModel):
    url: str
    video_format_id: str | None = None
    audio_format_id: str | None = None

def get_ydl_opts():
    opts = {
        "quiet": True,
        "noplaylist": True,
    }
    # إذا كان ملف الكوكيز موجوداً، نستخدمه
    if os.path.exists(COOKIES_FILE_PATH):
        opts["cookiefile"] = COOKIES_FILE_PATH
    return opts

@app.post("/formats")
def get_formats(data: FormatRequest):
    try:
        ydl_opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)

        video_formats = []
        audio_formats = []

        for f in info.get("formats", []):
            # Video
            if f.get("vcodec") != "none":
                video_formats.append({
                    "format_id": f["format_id"],
                    "height": f.get("height"),
                    "note": f.get("format_note"),
                    "ext": f.get("ext"),
                    "has_audio": f.get("acodec") != "none"
                })

            # Audio
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                audio_formats.append({
                    "format_id": f["format_id"],
                    "abr": f.get("abr"),
                    "ext": f.get("ext")
                })

        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "video_formats": video_formats,
            "audio_formats": audio_formats
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/stream")
def get_stream(data: StreamRequest):
    try:
        ydl_opts = get_ydl_opts()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)
            formats = info.get("formats", [])

        video_url = None
        audio_url = None

        if data.video_format_id:
            for f in formats:
                if f["format_id"] == data.video_format_id:
                    video_url = f["url"]
                    break
        
        if data.audio_format_id:
            for f in formats:
                if f["format_id"] == data.audio_format_id:
                    audio_url = f["url"]
                    break

        if not video_url and not audio_url:
             return {"message": "Please specify format_ids"}

        return {
            "video_stream_url": video_url,
            "audio_stream_url": audio_url
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))