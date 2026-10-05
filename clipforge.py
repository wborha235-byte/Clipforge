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

def transcribe_words(path):
    """Returns list of (word, start, end) synced to voice"""
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    # word_timestamps = True is the key for following voice
    segments, _ = model.transcribe(path, word_timestamps=True, beam_size=1, vad_filter=True)
    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                if w.word.strip():
                    words.append((w.word.strip(), w.start, w.end))
        else:
            # fallback if no word timestamps
            words.append((seg.text.strip(), seg.start, seg.end))
    print(f"Got {len(words)} words: {words[:10]}")
    return words

def make_ass_word_sync(words, clip_start, clip_end, ass_path):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCut,DejaVu Sans,90,&H00FFFF00,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,2,2,10,10,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600)//60)
        s = int(t % 60)
        cs = int((t*100)%100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = ""
    # Group 2-3 words per caption for viral style
    i = 0
    while i < len(words):
        chunk_words = []
        chunk_start = None
        chunk_end = None

        # Take 2-3 words
        for j in range(3):
            if i+j >= len(words): break
            w, ws, we = words[i+j]
            if we < clip_start or ws > clip_end: continue
            if chunk_start is None: chunk_start = ws
            chunk_end = we
            chunk_words.append(w)
            # Break on punctuation
            if w.endswith(('.',',','?','!')): break

        if not chunk_words:
            i += 1
            continue

        rs = max(0, chunk_start - clip_start)
        re = max(rs+0.4, chunk_end - clip_start) # min 0.4s visible

        text = " ".join(chunk_words).upper().strip()
        text = text.replace(" "," ")
        if text:
            events += f"Dialogue: 0,{fmt(rs)},{fmt(re)},CapCut,,0,0,0,,{text}\n"

        i += len(chunk_words)

    if not events:
        events = "Dialogue: 0,0:00:00.00,0:00:04.00,CapCut,,0,0,0,,TINY BAG THAT I CLIP ONTO MY BIG BAG\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + events)

def process_video(video_path):
    tmpdir = tempfile.mkdtemp()
    w, h, duration = get_video_info(video_path)
    words = transcribe_words(video_path)

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
        ass