import os, tempfile
from pathlib import Path
import numpy as np

def get_face_center_x_mediapipe(video_path):
    """Find where face is - returns smoothed center x"""
    import cv2
    import mediapipe as mp
    mp_face = mp.solutions.face_detection
    cap = cv2.VideoCapture(video_path)
    centers = []
    frame_idx = 0
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as detector:
        while True:
            ret, frame = cap.read()
            if not ret: break
            # Check every 5 frames for speed
            if frame_idx % 5 == 0:
                h,w,_ = frame.shape
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.process(rgb)
                if result.detections:
                    # Take first face
                    box = result.detections[0].location_data.relative_bounding_box
                    cx = (box.xmin + box.width/2) * w
                    centers.append(cx)
                else:
                    # No face, keep last
                    if centers: centers.append(centers[-1])
            frame_idx += 1
    cap.release()
    if not centers:
        return None
    # Smooth centers
    return int(np.median(centers))

def process_video(video_path):
    from moviepy.editor import VideoFileClip
    import cv2

    tmpdir = tempfile.mkdtemp()
    clips = []

    # 1. Find face position in full video
    face_x = get_face_center_x_mediapipe(video_path)

    with VideoFileClip(video_path) as clip:
        w,h = clip.size
        duration = clip.duration

        # 9:16 dimensions
        target_ratio = 9/16
        crop_h = h
        crop_w = int(crop_h * target_ratio)

        # Calculate x1 based on face, not center
        if face_x is not None:
            x1 = int(face_x - crop_w/2)
        else:
            x1 = (w - crop_w)//2

        # Keep inside video
        x1 = max(0, min(x1, w - crop_w))
        x2 = x1 + crop_w

        print(f"Face at {face_x}, cropping x1={x1} to x2={x2} from width {w}")

        clip_len = min(25, duration/5)
        for i in range(4):
            start = (duration / 5) * (i+0.5)
            end = min(start + clip_len, duration)
            if end > duration: break

            out = f"{tmpdir}/clip_{i}.mp4"
            sub = clip.subclip(start, end)
            # NO STRETCH - crop first, then resize keeping aspect
            cropped = sub.crop(x1=x1, x2=x2, y1=0, y2=h)
            # Resize to 1080x1920 - this is exact 9:16, so no stretch
            final = cropped.resize(newsize=(1080, 1920))
            final.write_videofile(out, codec='libx264', audio_codec='aac', fps=24, logger=None)
            clips.append(out)
            sub.close()
    return clips

def run_clipforge(url):
    import yt_dlp
    tmpdir = tempfile.mkdtemp()
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio/best[ext=mp4]/best',
        'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        for f in Path(tmpdir).glob('*.*'):
            if f.suffix in ['.mp4','.mkv','.webm']: return process_video(str(f))
    raise Exception("Download failed")

def run_clipforge_from_file(file_path):
    return process_video(file_path)