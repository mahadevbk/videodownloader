import streamlit as st
import pytube
import yt_dlp
from io import BytesIO
import re

st.title("Video Downloader")
st.write("Paste a video URL from YouTube, Facebook, Instagram, or other supported platforms to download.")

# Input field for URL
url = st.text_input("Enter Video URL")

def is_youtube_url(url):
    """Check if the URL is from YouTube."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return bool(re.match(youtube_regex, url))

def download_youtube_video(url):
    """Download a YouTube video using pytube."""
    try:
        yt = pytube.YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            return None, "No suitable video stream found."
        video_data = BytesIO()
        stream.stream_to_buffer(video_data)
        video_data.seek(0)
        return video_data, stream.default_filename
    except Exception as e:
        return None, f"Error downloading YouTube video: {str(e)}"

def download_with_ytdlp(url):
    """Download a video using yt-dlp for non-YouTube platforms."""
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '-',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_data = BytesIO()
            ydl.download_with_info_file(video_data, info)
            video_data.seek(0)
            filename = info.get('title', 'video') + '.mp4'
            return video_data, filename
    except Exception as e:
        return None, f"Error downloading video: {str(e)}"

if url:
    if st.button("Download Video"):
        with st.spinner("Downloading..."):
            if is_youtube_url(url):
                video_data, filename_or_error = download_youtube_video(url)
            else:
                video_data, filename_or_error = download_with_ytdlp(url)

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