import os, tempfile
from pathlib import Path

def process_video(video_path):
    from moviepy.editor import VideoFileClip

    tmpdir = tempfile.mkdtemp()
    clips = []

    with VideoFileClip(video_path) as clip:
        w,h = clip.size
        duration = clip.duration
        print(f"Original: {w}x{h}, duration {duration}")

        # --- NO STRETCH 9:16 CROP ---
        # Calculate 9:16 crop that keeps height full
        target_w = int(h * 9/16)
        # If video is already vertical (like yours), keep it as is
        if w < h: # Already vertical
            x1, x2 = 0, w
            crop_w = w
            crop_h = h
        else: # Horizontal, crop center to 9:16
            crop_w = target_w
            crop_h = h
            x1 = (w - crop_w)//2
            x2 = x1 + crop_w

        x1 = max(0, x1)
        x2 = min(w, x2)

        clip_len = min(20, duration/4.5)
        for i in range(4):
            start = (duration / 5) * (i+0.5)
            end = min(start + clip_len, duration)
            if end-start < 2: break
            if end > duration: break

            out = f"{tmpdir}/clip_{i}.mp4"
            sub = clip.subclip(start, end)
            # Crop to 9:16 without stretching
            cropped = sub.crop(x1=x1, x2=x2, y1=0, y2=h)
            # Resize keeping 9:16 ratio -> 1080x1920
            final = cropped.resize(height=1920)
            # Center pad width to 1080 if needed
            if final.w!= 1080:
                final = final.resize(width=1080)
            final.write_videofile(out, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', logger=None)
            clips.append(out)
            sub.close()
            cropped.close()
            final.close()
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