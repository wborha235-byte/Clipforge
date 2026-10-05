import os, tempfile, subprocess, json
from pathlib import Path
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def get_video_info(path):
    # Use opencv to get size/duration
    import cv2
    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frames / fps if fps else 0
    cap.release()
    if duration == 0:
        # fallback: try ffprobe
        duration = 30
    return w, h, duration

def process_video(video_path):
    tmpdir = tempfile.mkdtemp()
    w, h, duration = get_video_info(video_path)
    print(f"Video {w}x{h} dur {duration}")

    # Calculate 9:16 crop
    if w < h: # already vertical like your mov
        crop_w, crop_h = w, h
        x, y = 0, 0
        scale_filter = "scale=1080:1920:flags=lanczos"
    else:
        crop_h = h
        crop_w = int(h * 9/16)
        x = (w - crop_w)//2
        y = 0
        scale_filter = "scale=1080:1920:flags=lanczos"

    crop_filter = f"crop={crop_w}:{crop_h}:{x}:{y}"

    clips = []
    clip_len = min(20, duration/4.5)
    for i in range(4):
        start = (duration / 5) * (i+0.5)
        if start + 2 >= duration: break
        end = min(start + clip_len, duration)
        dur = end - start

        out = f"{tmpdir}/clip_{i}.mp4"
        cmd = [
            FFMPEG, "-y",
            "-ss", str(start),
            "-t", str(dur),
            "-i", video_path,
            "-vf", f"{crop_filter},{scale_filter}",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clips.append(out)
    return clips

def run_clipforge(url):
    import yt_dlp
    tmpdir = tempfile.mkdtemp()
    ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'{tmpdir}/%(id)s.%(ext)s', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        for f in Path(tmpdir).glob('*.*'):
            if f.suffix.lower() in ['.mp4','.mov','.mkv','.webm']:
                return process_video(str(f))
    raise Exception("Download failed")

def run_clipforge_from_file(file_path):
    return process_video(file_path)