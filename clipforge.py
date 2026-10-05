import os, re, tempfile
from pathlib import Path
import yt_dlp
import numpy as np

def download_youtube(url, tmpdir):
    # FIX for YouTube 403 on cloud servers
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # THIS FIXES THE 403
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip',
        },
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        # Find actual downloaded file
        for f in Path(tmpdir).glob('*.*'):
            if f.suffix in ['.mp4','.mkv','.webm']:
                return str(f), info
        return filepath, info

def run_clipforge(url):
    import cv2
    import mediapipe as mp
    from faster_whisper import WhisperModel
    from moviepy.editor import VideoFileClip
    
    tmpdir = tempfile.mkdtemp()
    video_path, info = download_youtube(url, tmpdir)
    
    if not os.path.exists(video_path):
        raise Exception(f"Download failed: {video_path}")
    
    # Transcribe
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, word_timestamps=True)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append((w.word, w.start, w.end))
    
    if not words:
        words = [("clip", 0, 10)]
    
    # Simple viral clip detection - 4 clips of 15-30 sec
    duration = VideoFileClip(video_path).duration
    clips = []
    clip_len = min(25, duration/5)
    
    for i in range(4):
        start = (duration / 5) * (i+0.5)
        end = min(start + clip_len, duration)
        
        clip_path = f"{tmpdir}/clip_{i}.mp4"
        # Basic center crop to 9:16 with face tracking simplified
        # For now just crop - full face tracking after first success
        with VideoFileClip(video_path).subclip(start, end) as v:
            w, h = v.size
            # 9:16 crop
            new_w = int(h * 9/16)
            x1 = (w - new_w)//2
            x2 = x1 + new_w
            cropped = v.crop(x1=x1, x2=x2, y1=0, y2=h)
            # Resize to 1080x1920
            final = cropped.resize((1080, 1920))
            final.write_videofile(clip_path, codec='libx264', audio_codec='aac', fps=24, logger=None)
            clips.append(clip_path)
    
    return clips