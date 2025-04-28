import streamlit as st
import pytube
import yt_dlp
from io import BytesIO
import re
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

st.title("Video Downloader")
st.write("Paste a video URL from YouTube, Facebook, Instagram, or other supported platforms to download.")

# Input field for URL
url = st.text_input("Enter Video URL")

# Option to use browser cookies
use_cookies = st.checkbox("Use browser cookies for private/restricted videos")
browser = None
if use_cookies:
    browser = st.selectbox("Select browser", ["firefox", "chrome", "safari", "edge", "opera"], index=0)

def is_youtube_url(url):
    """Check if the URL is from YouTube."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return bool(re.match(youtube_regex, url))

def download_youtube_video(url, use_cookies=False, browser=None):
    """Download a YouTube video using pytube, fallback to yt-dlp if it fails."""
    # Try pytube first
    try:
        logger.debug(f"Attempting pytube for YouTube video: {url}")
        yt = pytube.YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            logger.warning("No suitable video stream found with pytube, falling back to yt-dlp.")
            return download_with_ytdlp(url, use_cookies, browser)  # Fallback to yt-dlp
        logger.debug(f"Selected stream: {stream}")
        video_data = BytesIO()
        stream.stream_to_buffer(video_data)
        video_data.seek(0)
        return video_data, stream.default_filename
    except Exception as e:
        logger.error(f"pytube failed: {str(e)}. Falling back to yt-dlp.")
        # Fallback to yt-dlp
        return download_with_ytdlp(url, use_cookies, browser)

def download_with_ytdlp(url, use_cookies=False, browser=None):
    """Download a video using yt-dlp for non-YouTube platforms or as fallback."""
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '-',  # Output to buffer
            'quiet': False,
            'verbose': True,  # Enable verbose output for debugging
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'logger': logger,  # Log yt-dlp output
        }
        # Add cookies-from-browser if enabled
        if use_cookies and browser:
            ydl_opts['cookiesfrombrowser'] = browser  # Pass browser name as string

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_data = BytesIO()
            ydl.download_with_info_file(video_data, info)
            video_data.seek(0)
            filename = info.get('title', 'video') + '.mp4'
            return video_data, filename
    except Exception as e:
        logger.error(f"yt-dlp failed: {str(e)}")
        return None, f"Error downloading video: {str(e)}"

if url:
    if st.button("Download Video"):
        with st.spinner("Downloading..."):
            if is_youtube_url(url):
                video_data, filename_or_error = download_youtube_video(url, use_cookies, browser)
            else:
                video_data, filename_or_error = download_with_ytdlp(url, use_cookies, browser)

            if video_data:
                st.success("Download successful!")
                st.download_button(
                    label="Click to save video",
                    data=video_data,
                    file_name=filename_or_error,
                    mime="video/mp4"
                )
            else:
                st.error(filename_or_error)
                st.text("Verbose error output logged to console. Check terminal for details.")
