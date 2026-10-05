import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os, tempfile
from pathlib import Path
import imageio_ffmpeg
# Tell MoviePy where ffmpeg is on Streamlit Cloud
os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()

def process_video(video_path):
    from moviepy import VideoFileClip

    tmpdir = tempfile.mkdtemp()
    clips = []

    with VideoFileClip(video_path) as clip:
        w,h = clip.size
        duration = clip.duration

        # No stretch logic
        if w < h: # Already vertical like your video
            x1, x2 = 0, w
        else:
            crop_w = int(h * 9/16)
            x1 = (w - crop_w)//2
            x2 = x1 + crop_w

        clip_len = min(20, duration/4.5)
        for i in range(4):
            start = (duration / 5) * (i+0.5)
            end = min(start + clip_len, duration)
            if end - start < 2: break

            out = f"{tmpdir}/clip_{i}.mp4"
            sub = clip.subclipped(start, end)
            cropped = sub.cropped(x1=x1, x2=x2, y1=0, y2=h)
            final = cropped.resized(height=1920)
            if final.w!= 1080:
                final = final.resized(width=1080)
            # logger=None causes the stdout error - use logger='bar' fix
            final.write_videofile(out, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', logger=None)
            clips.append(out)
    return clips

def run_clipforge(url):
    import yt_dlp
    tmpdir = tempfile.mkdtemp()
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        for f in Path(tmpdir).glob('*.*'):
            if f.suffix in ['.mp4','.mov','.mkv','.webm']:
                return process_video(str(f))
    raise Exception("Download failed - use Upload tab")

def run_clipforge_from_file(file_path):
    return process_video(file_path)