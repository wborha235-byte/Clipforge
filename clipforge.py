import os, tempfile
from pathlib import Path
import yt_dlp

def download_youtube(url, tmpdir):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'http_headers': {'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12) gzip'},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        for f in Path(tmpdir).glob('*.*'):
            if f.suffix in ['.mp4','.mkv','.webm']:
                return str(f)
        return ydl.prepare_filename(info)

def process_video(video_path):
    from faster_whisper import WhisperModel
    from moviepy.editor import VideoFileClip
    tmpdir = tempfile.mkdtemp()
    clips = []
    with VideoFileClip(video_path) as clip:
        duration = clip.duration
        clip_len = min(25, duration/5)
        for i in range(4):
            start = (duration / 5) * (i+0.5)
            end = min(start + clip_len, duration)
            if end > duration: break
            out = f"{tmpdir}/clip_{i}.mp4"
            sub = clip.subclip(start, end)
            w,h = sub.size
            new_w = int(h*9/16)
            x1 = (w-new_w)//2
            cropped = sub.crop(x1=x1, x2=x1+new_w, y1=0, y2=h)
            final = cropped.resize((1080,1920))
            final.write_videofile(out, codec='libx264', audio_codec='aac', fps=24, logger=None)
            clips.append(out)
    return clips

def run_clipforge(url):
    tmpdir = tempfile.mkdtemp()
    vp = download_youtube(url, tmpdir)
    return process_video(vp)

def run_clipforge_from_file(file_path):
    return process_video(file_path)