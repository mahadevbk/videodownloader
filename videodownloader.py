import streamlit as st
import pytube
import yt_dlp
import tempfile
import os
from io import BytesIO
import re
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# App Title
st.set_page_config(page_title="Dev's Video Downloader", page_icon="🎥")
st.title("🎥 Dev's Video Downloader")
st.write("Paste a video URL from YouTube, Facebook, Instagram, or other supported platforms to download.")

# Input field for URL
url = st.text_input("Enter Video URL")

# Option to use browser cookies
use_cookies = st.checkbox("Use browser cookies for private/restricted videos")
browser = None
if use_cookies:
    browser = st.selectbox("Select browser", ["firefox", "chrome", "safari", "edge", "opera"], index=0)

# Audio-only download mode
audio_only = st.checkbox("Download as audio (MP3)", value=False)

# Option to list formats on failure
list_formats = st.checkbox("Show available formats if download fails", value=True)

def is_youtube_url(url):
    """Check if the URL is from YouTube."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return bool(re.match(youtube_regex, url))

def fetch_formats_for_selection(url, use_cookies=False, browser=None, audio_only=False):
    """Fetch available formats and return a list of tuples (id, description)."""
    try:
        ydl_opts = {
            'quiet': True,
            'logger': logger,
        }
        if use_cookies and browser:
            ydl_opts['cookiesfrombrowser'] = browser

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            format_list = []
            for f in formats:
                format_id = f.get('format_id', '')
                ext = f.get('ext', '')
                if audio_only:
                    if f.get('vcodec') == 'none':
                        abr = f.get('abr', 'unknown')
                        filesize = f.get('filesize') or 0
                        size_mb = f"{round(filesize / 1024 / 1024, 1)}MB" if filesize else "unknown size"
                        format_list.append((format_id, f"{ext.upper()} {abr}kbps ({size_mb})"))
                else:
                    if f.get('vcodec') != 'none':
                        resolution = f.get('format_note', '') or f.get('height', 'unknown')
                        filesize = f.get('filesize') or 0
                        size_mb = f"{round(filesize / 1024 / 1024, 1)}MB" if filesize else "unknown size"
                        format_list.append((format_id, f"{ext.upper()} {resolution} ({size_mb})"))

            return format_list
    except Exception as e:
        logger.error(f"Failed to fetch formats: {str(e)}")
        return []

def download_with_ytdlp(url, use_cookies=False, browser=None, specific_format=None, audio_only=False):
    """Download video or audio with yt-dlp."""
    try:
        tmpdir = tempfile.mkdtemp()
        output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            'format': specific_format or ('bestaudio/best' if audio_only else 'bestvideo+bestaudio/best'),
            'outtmpl': output_template,
            'quiet': False,
            'verbose': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'logger': logger,
            'postprocessors': [],
        }

        if audio_only:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })

        if use_cookies and browser:
            ydl_opts['cookiesfrombrowser'] = browser

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Find downloaded file
        video_filename = None
        for f in os.listdir(tmpdir):
            if audio_only and f.endswith('.mp3'):
                video_filename = os.path.join(tmpdir, f)
                break
            elif not audio_only and f.endswith(('.mp4', '.mkv', '.webm')):
                video_filename = os.path.join(tmpdir, f)
                break

        if not video_filename:
            return None, "Downloaded file not found.", None

        video_file = open(video_filename, 'rb')
        filename = os.path.basename(video_filename)

        return video_file, filename, tmpdir

    except Exception as e:
        logger.error(f"yt-dlp download failed: {str(e)}")
        return None, f"Error downloading file: {str(e)}", None

def download_youtube_video(url, use_cookies=False, browser=None, specific_format=None, audio_only=False):
    """Download YouTube video using pytube first, fallback to yt-dlp."""
    if audio_only:
        return download_with_ytdlp(url, use_cookies, browser, specific_format, audio_only)

    try:
        logger.debug(f"Attempting pytube for YouTube video: {url}")
        yt = pytube.YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            logger.warning("No suitable video stream found with pytube, falling back to yt-dlp.")
            return download_with_ytdlp(url, use_cookies, browser, specific_format, audio_only)
        logger.debug(f"Selected stream: {stream}")
        video_data = BytesIO()
        stream.stream_to_buffer(video_data)
        video_data.seek(0)
        return video_data, stream.default_filename, None
    except Exception as e:
        logger.error(f"pytube failed: {str(e)}. Falling back to yt-dlp.")
        return download_with_ytdlp(url, use_cookies, browser, specific_format, audio_only)

# -- Main App logic --

selected_format_id = None

if url:
    formats = fetch_formats_for_selection(url, use_cookies, browser, audio_only=audio_only)
    
    if formats:
        st.subheader("Available Formats")
        format_options = {desc: fid for fid, desc in formats}
        selected_desc = st.selectbox("Choose format", list(format_options.keys()))
        selected_format_id = format_options[selected_desc]
    else:
        st.warning("No available formats or failed to fetch formats.")

    if st.button("Download"):
        with st.spinner("Downloading..."):
            if is_youtube_url(url):
                video_data, filename_or_error, tmpdir = download_youtube_video(url, use_cookies, browser, specific_format=selected_format_id, audio_only=audio_only)
            else:
                video_data, filename_or_error, tmpdir = download_with_ytdlp(url, use_cookies, browser, specific_format=selected_format_id, audio_only=audio_only)

            if video_data:
                st.success("✅ Download successful!")
                mime_type = "audio/mpeg" if audio_only else "video/mp4"
                st.download_button(
                    label="Click to save file",
                    data=video_data,
                    file_name=filename_or_error,
                    mime=mime_type
                )
                if tmpdir:
                    video_data.close()
                    shutil.rmtree(tmpdir, ignore_errors=True)
            else:
                if "Video unavailable" in filename_or_error or "This video is not available" in filename_or_error:
                    st.error("⚠️ The video is not available (deleted, private, blocked). Please check the URL.")
                else:
                    st.error(filename_or_error)
                st.text("Verbose error output logged to console. Check terminal for details.")
