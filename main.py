from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube Stream API")

class FormatRequest(BaseModel):
    url: str

class StreamRequest(BaseModel):
    url: str
    video_format_id: str | None = None
    audio_format_id: str | None = None

# ====== 1) Get formats (نفس الكود السابق مع تحسين بسيط) ======
@app.post("/formats")
def get_formats(data: FormatRequest):
    try:
        # يفضل استخدام 'noplaylist' لتسريع العملية
        ydl_opts = {"quiet": True, "noplaylist": True}
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
                    "note": f.get("format_note"), # مفيد لمعرفة الجودة
                    "ext": f.get("ext"),
                    "has_audio": f.get("acodec") != "none" # مهم جداً
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


# ====== 2) Get direct stream URL (التصحيح هنا) ======
@app.post("/stream")
def get_stream(data: StreamRequest):
    try:
        ydl_opts = {
    "quiet": True,
    "noplaylist": True,
    "cookiefile": "cookies.txt"  # إضافة هذا السطر
}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)
            formats = info.get("formats", [])

        video_url = None
        audio_url = None

        # البحث عن رابط الفيديو المطلوب
        if data.video_format_id:
            for f in formats:
                if f["format_id"] == data.video_format_id:
                    video_url = f["url"]
                    break
        
        # البحث عن رابط الصوت المطلوب
        if data.audio_format_id:
            for f in formats:
                if f["format_id"] == data.audio_format_id:
                    audio_url = f["url"]
                    break

        # حالة خاصة: إذا لم يحدد المستخدم فورمات، نرجع أفضل شيء مدمج (progressive) إن وجد
        if not video_url and not audio_url:
             # هذا الخيار يعيد رابط واحد يحتوي صوت وصورة (عادة جودة 720 أو 360)
             # لكنه نادراً ما يكون متاحاً للجودات العالية 1080 وما فوق
             return {"message": "Please specify format_ids or handle default logic"}

        return {
            "video_stream_url": video_url,
            "audio_stream_url": audio_url,
            "note": "For high quality, client must play video and audio streams together."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
