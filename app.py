import streamlit as st
import tempfile
from pathlib import Path

st.set_page_config(page_title="ClipForge", page_icon="🔥", layout="centered")
st.title("ClipForge 🔥")
st.write("Upload up to 2GB or paste YouTube link → 10 viral Reels")

tab1, tab2 = st.tabs(["📤 Upload Video", "🔗 YouTube Link"])

with tab1:
    uploaded = st.file_uploader("Upload MP4 / MOV (up to 2GB)", type=["mp4","mov","mkv","webm","m4v"])
    num_clips1 = st.slider("How many clips?", 4, 12, 10, key="n1")
    clip_len1 = st.slider("Clip length (sec)", 15, 40, 20, key="l1")

    if uploaded:
        size_mb = uploaded.size / (1024*1024)
        st.write(f"📁 {uploaded.name} - {size_mb:.1f} MB")
        st.video(uploaded)
        if st.button(f"🔥 FORGE {num_clips1} CLIPS", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            with st.spinner(f"Processing {size_mb:.0f}MB... (3-5 mins for 20min)"):
                try:
                    from clipforge import run_clipforge_from_file
                    clips = run_clipforge_from_file(tmp_path, num_clips=num_clips1, clip_len=clip_len1)
                    st.success(f"Done! {len(clips)} clips")
                    for i, c in enumerate(clips):
                        st.video(c)
                        with open(c, "rb") as f:
                            st.download_button(f"Download Clip {i+1}", f, file_name=f"viral_clip_{i+1}.mp4", key=f"up{i}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

with tab2:
    st.write("Paste any YouTube link - works even for 1 hour videos")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    num_clips2 = st.slider("How many clips?", 4, 12, 10, key="n2")
    clip_len2 = st.slider("Clip length (sec)", 15, 40, 20, key="l2")

    if st.button("🔥 FORGE FROM YOUTUBE", type="primary", use_container_width=True) and url:
        with st.spinner("Downloading YouTube + transcribing... (takes 2-4 mins)"):
            try:
                from clipforge import run_clipforge
                clips = run_clipforge(url, num_clips=num_clips2, clip_len=clip_len2)
                st.success(f"Done! {len(clips)} clips from YouTube")
                for i, c in enumerate(clips):
                    st.video(c)
                    with open(c, "rb") as f:
                        st.download_button(f"Download Clip {i+1}", f, file_name=f"yt_clip_{i+1}.mp4", key=f"yt{i}", use_container_width=True)
            except Exception as e:
                st.error(f"YouTube Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                st.info("Tip: If YouTube blocks, set video to Unlisted and try again, or download video and use Upload tab.")