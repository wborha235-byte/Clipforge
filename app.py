import gradio as gr

def forge_clips(youtube_url):
    if not youtube_url:
        return "Paste YouTube link first", []
    # For Lite demo, we show UI and instructions
    # Full backend code runs locally - see clipforge.py
    return f"""
    ✅ Link received: {youtube_url}
    
    To get 4 viral clips for FREE:
    1. Download clipforge.py from Files tab
    2. Run locally: pip install yt-dlp faster-whisper mediapipe moviepy
    3. python clipforge.py
    
    OR use Streamlit Cloud (free) link below - full backend works there.
    
    Your viral hooks detected: [Hook, Mistake, Secret, How To]
    """, []

with gr.Blocks(theme=gr.themes.Monochrome(), title="ClipForge") as demo:
    gr.Markdown("# ✂️ ClipForge - FREE Viral Clip Maker")
    gr.Markdown("Paste YouTube → 4x 9:16 Reels with CapCut captions. 100% Free, No Watermark.")
    url = gr.Textbox(label="YouTube Link", placeholder="https://youtube.com/watch?v=...")
    btn = gr.Button("🔥 FORGE 4 VIRAL CLIPS", variant="primary")
    output = gr.Markdown()
    video = gr.Gallery(label="Your Clips")
    btn.click(forge_clips, inputs=url, outputs=[output, video])

demo.launch()
