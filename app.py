import streamlit as st
import tempfile
from pathlib import Path

st.set_page_config(page_title="ClipForge", page_icon="🔥", layout="centered")
st.title("ClipForge 🔥")
st.caption("20-min video → 10 viral 9:16 clips with yellow captions")

tab1, tab2 = st.tabs(["📤 Upload Video (2GB)", "🔗 YouTube Link"])

with tab1:
    f = st.file_uploader("Upload MP4/MOV/MKV", type=["mp4","mov","mkv","webm","m4v"])
    n1 = st.slider("Clips", 4, 12, 10, key="n1")
    l1 = st.slider("Length sec", 15, 40, 20, key="l1")
    if f:
        st.video(f)
        st.write(f"{f.name} - {f.size/1024/1024:.1f} MB")
        if st.button(f"🔥 FORGE {n1} CLIPS", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                tmp.write(f.read())
                p = tmp.name
            with st.spinner("Transcribing + cutting... 3-5 mins"):
                try:
                    from clipforge import run_clipforge_from_file
                    clips = run_clipforge_from_file(p, num_clips=n1, clip_len=l1)
                    st.success(f"Done {len(clips)} clips!")
                    for i,c in enumerate(clips):
                        st.video(c)
                        with open(c,"rb") as fd:
                            st.download_button(f"Download {i+1}", fd, file_name=f"clip_{i+1}.mp4", key=f"u{i}", use_container_width=True)
                except Exception as e:
                    st.error(str(e))
                    import traceback; st.code(traceback.format_exc())

with tab2:
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    n2 = st.slider("Clips", 4, 12, 10, key="n2")
    l2 = st.slider("Length sec", 15, 40, 20, key="l2")
    if st.button("🔥 FORGE FROM YOUTUBE", type="primary", use_container_width=True) and url:
        with st.spinner("Downloading YouTube... (may 403 block - if so use Upload tab)"):
            try:
                from clipforge import run_clipforge
                clips = run_clipforge(url, num_clips=n2, clip_len=l2)
                st.success(f"Done {len(clips)} clips!")
                for i,c in enumerate(clips):
                    st.video(c)
                    with open(c,"rb") as fd:
                        st.download_button(f"Download {i+1}", fd, file_name=f"yt_{i+1}.mp4", key=f"y{i}", use_container_width=True)
            except Exception as e:
                st.error(str(e))
                st.info("Fix: YouTube blocks Streamlit IP with 403. Download video to phone then use Upload tab - works 100%")