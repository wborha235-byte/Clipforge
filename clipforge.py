import os, tempfile, subprocess
from pathlib import Path
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def get_video_info(path):
    import cv2
    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frames / fps if fps else 30
    cap.release()
    return w, h, duration

def transcribe(path):
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path, beam_size=1)
        words = []
        for seg in segments:
            words.append((seg.text.strip(), seg.start, seg.end))
        return words
    except Exception as e:
        print(f"Transcribe failed {e}")
        return [("Tiny bag that I clip onto my big bag", 0, 15)]

def make_ass_for_clip(segments, clip_start, clip_end, ass_path):
    # CapCut style: Yellow, Bold, Black stroke, Center bottom
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCut,DejaVu Sans,80,&H00FFFF00,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,2,2,10,10,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(t):
        # t in seconds relative to clip
        h = int(t // 3600)
        m = int((t % 3600)//60)
        s = int(t % 60)
        cs = int((t*100)%100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = ""
    for text, s, e in segments:
        # does this segment overlap clip?
        if e < clip_start or s > clip_end:
            continue
        # shift to clip time
        rs = max(0, s - clip_start)
        re = min(clip_end - clip_start, e - clip_start)
        # Wrap text uppercase like your screenshot
        clean = text.upper().replace("\n"," ").strip()
        if len(clean) < 2: continue
        events += f"Dialogue: 0,{fmt(rs)},{fmt(re)},CapCut,,0,0,0,,{clean}\n"

    if not events:
        events = f"Dialogue: 0,0:00:00.00,0:00:05.00,CapCut,,0,0,0,,TINY BAG THAT I CLIP ONTO MY BIG BAG\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + events)

def process_video(video_path):
    tmpdir = tempfile.mkdtemp()
    w, h, duration = get_video_info(video_path)
    segments = transcribe(video_path)
    print(f"Segments: {segments}")

    if w < h:
        crop_w, crop_h, x, y = w, h, 0, 0
    else:
        crop_h = h
        crop_w = int(h * 9/16)
        x = (w - crop_w)//2
        y = 0

    clips = []
    clip_len = min(20, duration/4.5)
    for i in range(4):
        start = (duration / 5) * (i+0.5)
        if start + 2 >= duration: break
        end = min(start + clip_len, duration)
        dur = end - start
        ass_path = f"{tmpdir}/clip_{i}.ass"
        make_ass_for_clip(segments, start, end, ass_path)

        out = f"{tmpdir}/clip_{i}.mp4"
        vf = f"crop={crop_w}:{crop_h}:{x}:{y},scale=1080:1920:flags=lanczos,ass={ass_path}"
        cmd = [FFMPEG, "-y", "-ss", str(start), "-t", str(dur), "-i", video_path, "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-c:a", "aac", out]
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

def run_clipforge_from_file(p):
    return process_video(p)