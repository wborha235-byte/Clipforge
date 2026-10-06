import os, tempfile, subprocess, json
from pathlib import Path

def get_ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_info(path):
    # ffprobe without needing opencv
    FFMPEG = get_ffmpeg()
    ffprobe = FFMPEG.replace("ffmpeg", "ffprobe")
    try:
        cmd = [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration", "-of", "json", path]
        out = subprocess.check_output(cmd, text=True)
        j = json.loads(out)
        s = j['streams'][0]
        w = int(s.get('width', 1280))
        h = int(s.get('height', 720))
        dur = float(s.get('duration', 60))
        return w, h, dur
    except:
        import cv2
        cap = cv2.VideoCapture(path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        dur = frames / fps if frames else 60.0
        cap.release()
        return w, h, dur

def transcribe(path):
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segs, _ = model.transcribe(path, word_timestamps=True, beam_size=1, vad_filter=True)
        out=[]
        for s in segs:
            if s.words:
                for w in s.words:
                    if w.word.strip(): out.append((w.word.strip(), float(w.start), float(w.end)))
            else:
                if s.text.strip(): out.append((s.text.strip(), float(s.start), float(s.end)))
        return out if out else [("VIRAL CLIP", 0, 30)]
    except Exception as e:
        print(e)
        return [("VIRAL", 0, 2), ("CLIP", 2, 4)]

def make_ass(words, cs, ce, ass_path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCut,Arial,80,&H00FFFF00,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,1,2,2,10,10,400,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(t):
        h=int(t//3600); m=int((t%3600)//60); s=int(t%60); c=int((t*100)%100)
        return f"{h}:{m:02d}:{s:02d}.{c:02d}"
    ev=""; i=0
    while i < len(words):
        chunk=[]; st=None; en=None
        for k in range(3):
            if i+k>=len(words): break
            w,ws,we=words[i+k]
            if we<cs or ws>ce: continue
            if st is None: st=ws
            en=we; chunk.append(w)
        if not chunk: i+=1; continue
        rs=max(0,st-cs); re=max(rs+0.6,en-cs)
        ev+=f"Dialogue: 0,{fmt(rs)},{fmt(re)},CapCut,,0,0,0,,{' '.join(chunk).upper()}\n"
        i+=len(chunk)
    if not ev:
        ev="Dialogue: 0,0:00:00.00,0:00:05.00,CapCut,,0,0,0,,VIRAL MOMENT\n"
    open(ass_path,"w",encoding="utf-8").write(head+ev)

def process_video(video_path, num_clips=10, clip_len=20):
    FFMPEG=get_ffmpeg()
    tmp=tempfile.mkdtemp()
    w,h,dur=get_info(video_path)
    words=transcribe(video_path)
    cw,ch,x,y = (w,h,0,0) if w<h else (int(h*9/16),h,(w-int(h*9/16))//2,0)
    clips=[]
    step = dur / (num_clips + 1)
    for i in range(num_clips):
        s = step * (i+1)
        if s + 5 >= dur: break
        e = min(s + clip_len, dur)
        ass=f"{tmp}/c{i}.ass"
        make_ass(words,s,e,ass)
        out=f"{tmp}/clip_{i}.mp4"
        vf=f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,ass={ass}"
        cmd=[FFMPEG,"-y","-ss",str(s),"-t",str(e-s),"-i",video_path,"-vf",vf,"-c:v","libx264","-preset","ultrafast","-crf","23","-c:a","aac",out]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clips.append(out)
    return clips

def run_clipforge_from_file(p, num_clips=10, clip_len=20, **k):
    return process_video(p, num_clips, clip_len)

def run_clipforge(url, num_clips=10, clip_len=20, **k):
    import yt_dlp
    td=tempfile.mkdtemp()
    last=None
    for client in [['ios'], ['android'], ['web']]:
        try:
            opts={'format':'best[ext=mp4]/best','outtmpl':f'{td}/%(id)s.%(ext)s','quiet':True,'nocheckcertificate':True,'extractor_args':{'youtube':{'player_client':client}}}
            with yt_dlp.YoutubeDL(opts) as y:
                y.download([url])
                for f in Path(td).glob('*.*'):
                    if f.suffix.lower() in ['.mp4','.mov','.mkv','.webm','.m4v']:
                        return process_video(str(f), num_clips, clip_len)
        except Exception as e:
            last=e; continue
    raise Exception(f"YouTube 403 Blocked by Streamlit IP. Download video and use Upload tab. {last}")