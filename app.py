import streamlit as st, os
from pathlib import Path
st.set_page_config(page_title="ClipForge", page_icon="✂️", layout="centered")
st.markdown("<style>.stApp{background:#0a0a0a;color:white} div[data-testid='stButton'] button{background:#ff0050;color:white;border-radius:30px;padding:15px;width:100%;font-weight:900;font-size:20px}</style>", unsafe_allow_html=True)
st.title("✂️ ClipForge")
st.write("Paste YouTube → Get 4 viral Reels (9:16 + CapCut captions). Free, No Watermark.")

url = st.text_input("YouTube Link", placeholder="https://youtube.com/watch?v=...")

if st.button("🔥 FORGE 4 CLIPS"):
    if not url.strip():
        st.error("Paste a link")
    else:
        from clipforge import run_clipforge
        with st.spinner("Downloading... Transcribing... Face tracking... 2-3 mins first time"):
            try:
                clips = run_clipforge(url.strip())
                st.success(f"Done! {len(clips)} clips ready")
                for c in clips:
                    st.video(c)
                    with open(c, "rb") as f:
                        st.download_button(f"Download {Path(c).name}", f, file_name=Path(c).name, key=c)
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Try video under 10 mins for first test")

st.caption("Use only videos you own. Open-source: yt-dlp + faster-whisper + MediaPipe")