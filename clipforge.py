import os, re, tempfile
from pathlib import Path
import yt_dlp
from faster_whisper import WhisperModel
import numpy as np
# cv2 and mediapipe imported inside functions to avoid Streamlit crash

HOOK_WORDS = ["secret","stop","never","how to","mistake","truth","why","don't","most people","here's","watch this","you should"]

def download_yt(url, out_path="input.mp4"):
    if os.path.exists(out_path): os.remove(out_path)
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': out_path,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_path

def transcribe_with_words(video_path):
    segments, info = whisper_model.transcribe(video_path, word_timestamps=True, vad_filter=True)
    words = []
    full_text = ""
    for seg in segments:
        full_text += seg.text + " "
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return full_text, words

def score_viral_moments(full_text, words, num_clips=4, clip_len=35):
    sentences = []
    curr = {"text": "", "start": words[0]["start"], "end": 0}
    for w in words:
        curr["text"] += w["word"] + " "
        curr["end"] = w["end"]
        if len(curr["text"]) > 80 or "." in w["word"] or "?" in w["word"]:
            sentences.append(curr)
            curr = {"text": "", "start": w["end"], "end": w["end"]}
    scored = []
    for s in sentences:
        text = s["text"].lower()
        score = random.uniform(0,1)
        for hook in HOOK_WORDS:
            if hook in text: score += 3
        if "?" in text: score += 2
        scored.append({**s, "score": score})
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)
    clips, used = [], []
    for s in scored:
        start = max(0, s["start"] - 1)
        end = start + clip_len
        if end > words[-1]["end"]: continue
        if any(abs(start - u) < clip_len for u in used): continue
        clips.append({"start": start, "end": end, "hook": s["text"][:60]})
        used.append(start)
        if len(clips) >= num_clips: break
    if len(clips) < num_clips:
        total = words[-1]["end"]
        for i in range(num_clips - len(clips)):
            r = random.uniform(0, max(0, total - clip_len))
            clips.append({"start": r, "end": r+clip_len, "hook": "Highlight"})
    return sorted(clips, key=lambda x: x["start"])

def get_face_center_x(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face.process(rgb)
    if results.detections:
        box = results.detections[0].location_data.relative_bounding_box
        return box.xmin + box.width/2
    return 0.5

def create_vertical_clip(input_path, start, end, words_in_clip, output_path):
    clip = VideoFileClip(input_path).subclip(start, end)
    w, h = clip.size
    target_w, target_h = 1080, 1920
    # pre-scan faces
    face_xs = []
    cap = cv2.VideoCapture(input_path)
    for t in np.arange(start, end, 0.5):
        cap.set(cv2.CAP_PROP_POS_MSEC, t*1000)
        ret, frame = cap.read()
        if ret: face_xs.append(get_face_center_x(frame))
        else: face_xs.append(0.5)
    cap.release()
    def make_frame(t):
        frame = clip.get_frame(t)
        idx = min(int(t/0.5), len(face_xs)-1)
        center_x = face_xs[idx]
        crop_h = h
        crop_w = int(crop_h * 9/16)
        x_center_px = int(center_x * w)
        x1 = max(0, min(w - crop_w, x_center_px - crop_w//2))
        cropped = frame[:, x1:x1+crop_w]
        resized = cv2.resize(cropped, (target_w, target_h))
        return resized
    final_clip = VideoClip(make_frame, duration=clip.duration)
    # captions 3 words at a time
    txt_clips = []
    for i in range(0, len(words_in_clip), 3):
        chunk = words_in_clip[i:i+3]
        if not chunk: continue
        text = " ".join([c["word"] for c in chunk]).upper()
        t_start = max(0, chunk[0]["start"] - start)
        t_end = min(clip.duration, chunk[-1]["end"] - start)
        if t_end <= t_start: continue
        try:
            tc = TextClip(text, fontsize=70, color='white', font='DejaVu-Sans-Bold', stroke_color='black', stroke_width=6, method='caption', size=(900, None))
        except:
            tc = TextClip(text, fontsize=70, color='white', method='caption', size=(900, None))
        tc = tc.set_position(('center', 1250)).set_start(t_start).set_end(t_end)
        txt_clips.append(tc)
    final = CompositeVideoClip([final_clip] + txt_clips, size=(target_w, target_h))
    final.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', logger=None)
    return output_path

def run_clipforge(youtube_url):
    print(f"Downloading {youtube_url}")
    input_path = download_yt(youtube_url, "input.mp4")
    print("Transcribing...")
    full_text, words = transcribe_with_words(input_path)
    if not words: raise Exception("No speech detected")
    clips = score_viral_moments(full_text, words, num_clips=4, clip_len=32)
    results = []
    for i, c in enumerate(clips):
        words_in = [w for w in words if c["start"] <= w["start"] <= c["end"]]
        out_path = str(OUTPUT_DIR / f"clip_{i+1}_{int(c['start'])}s.mp4")
        print(f"Creating clip {i+1}: {c['hook']}")
        create_vertical_clip(input_path, c["start"], c["end"], words_in, out_path)
        results.append(out_path)
    return results
