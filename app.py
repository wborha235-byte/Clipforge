import streamlit as st, os, tempfile
from pathlib import Path
st.set_page_config(page_title="ClipForge", page_icon="✂️", layout="centered")
st.markdown("<style>.stApp{background:#0a0a0a;color:white} div[data-testid='stButton'] button{background:#ff0050;color:white;border-radius:30px;padding:15px;width:100%;font-weight:900;font-size:20px}</style>", unsafe_allow_html=True)
st.title("✂️ ClipForge")
st.write("Upload video → Get 4 viral Reels (9:16 + CapCut captions). Free.")

tab1, tab2 = st.tabs(["📤 Upload Video", "🔗 YouTube Link"])
uploaded = None
url = ""

with tab1:
    uploaded = st.file_uploader("Upload MP4 (from your gallery)", type=['mp4','mov','mkv'])
    
with tab2:
    url = st.text_input("YouTube Link (may need cookies due to YouTube block)", placeholder="https://youtube.com/watch?v=...")
    st.caption("YouTube blocks cloud IPs now. If it fails, use Upload tab.")

if st.button("🔥 FORGE 4 CLIPS"):
    if not uploaded and not url.strip():
        st.error("Upload a video or paste link")
    else:
        from clipforge import run_clipforge_from_file, run_clipforge
        with st.spinner("Processing... Face tracking + Captions... 2-3 mins"):
            try:
                if uploaded:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tmp.write(uploaded.read())
                    tmp.close()
                    clips = run_clipforge_from_file(tmp.name)
                else:
                    clips = run_clipforge(url.strip())
                    
                st.success(f"Done! {len(clips)} clips ready")
                for c in clips:
                    st.video(c)
                    with open(c, "rb") as f:
                        st.download_button(f"Download {Path(c).name}", f, file_name=Path(c).name, key=c)
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Tip: If YouTube fails, download video to phone first (using YouTube app -> Save), then upload it here. Same result.")