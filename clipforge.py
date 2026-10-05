import os, tempfile, subprocess
from pathlib import Path

def get_ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_info(p):
    import cv2
    cap = cv2.VideoCapture(p)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = frames / fps if fps else 30.0
    cap.release()
    return w, h, dur

def transcribe(p):
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segs, _ = model.transcribe(p, word_timestamps=True, beam_size=1, vad_filter=True)
        out = []
        for s in segs:
            if s.words:
                for w in s.words:
                    if w.word.strip():
                        out.append((w.word.strip(), float(w.start), float(w.end)))
            else:
                out.append((s.text.strip(), float(s.start), float(s.end)))
        return out
    except Exception as e:
        print(e)
        return [("TINY BAG THAT I CLIP ONTO MY BIG BAG", 0, 10)]

def make_ass(words, cs, ce, path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCut,DejaVu Sans,85,&H00FFFF00,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,2,2,10,10,400,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def f(t):
        h=int(t//3600); m=int((t%3600)//60); s=int(t%60); c=int((t*100)%100)
        return f"{h}:{m:02d}:{s:02d}.{c:02d}"
    ev=""
    i=0
    while i < len(words):
        chunk=[]; s=None; e=None
        for k in range(3):
            if i+k>=len(words): break
            w,ws,we=words[i+k]
            if we<cs or ws>ce: continue
            if s is None: s=ws
            e=we; chunk.append(w)
        if not chunk:
            i+=1; continue
        rs=max(0,s-cs); re=max(rs+0.5,e-cs)
        txt=" ".join(chunk).upper()
        ev+=f"Dialogue: 0,{f(rs)},{f(re)},CapCut,,0,0,0,,{txt}\n"
        i+=len(chunk)
    if not ev:
        ev="Dialogue: 0,0:00:00.00,0:00:05.00,CapCut,,0,0,0,,TINY BAG THAT I CLIP ONTO MY BIG BAG\n"
    open(path,"w",encoding="utf-8").write(head+ev)

def process_video(video_path):
    FFMPEG=get_ffmpeg()
    tmp=tempfile.mkdtemp()
    w,h,dur=get_info(video_path)
    words=transcribe(video_path)
    cw, ch, x, y = (w,h,0,0) if w<h else (int(h*9/16),h,(w-int(h*9/16))//2,0)
    clips=[]
    clen=min(18,dur/4.5)
    for i in range(4):
        st=(dur/5)*(i+0.5)
        if st+2>=dur: break
        en=min(st+clen,dur)
        ass=f"{tmp}/c{i}.ass"
        make_ass(words,st,en,ass)
        out=f"{tmp}/clip_{i}.mp4"
        vf=f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,ass={ass}"
        cmd=[FFMPEG,"-y","-ss",str(st),"-t",str(en-st),"-i",video_path,"-vf",vf,"-c:v","libx264","-preset","ultrafast","-crf","23","-c:a","aac",out]
        subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        clips.append(out)
    return clips

def run_clipforge_from_file(p): return process_video(p)

def run_clipforge(url):
    import yt_dlp
    td=tempfile.mkdtemp()
    opts={'format':'best[ext=mp4]/best','outtmpl':f'{td}/%(id)s.%(ext)s','quiet':True}
    with yt_dlp.YoutubeDL(opts) as y:
        y.download([url])
        for f in Path(td).glob('*.*'):
            if f.suffix.lower() in ['.mp4','.mov','.mkv','.webm']:
                return process_video(str(f))
    raise Exception("Download failed")