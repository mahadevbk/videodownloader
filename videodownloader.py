import tempfile
import os

def download_with_ytdlp(url, use_cookies=False, browser=None):
    """Download a video using yt-dlp for non-YouTube platforms or as fallback, optimized for large files."""
    format_options = [
        'bestvideo+bestaudio/best',
        'best'
    ]
    
    for fmt in format_options:
        try:
            tmpdir = tempfile.mkdtemp()  # Persistent temp folder until manual cleanup
            tmpfile_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
            ydl_opts = {
                'format': fmt,
                'outtmpl': tmpfile_template,
                'quiet': False,
                'verbose': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'logger': logger,
            }
            if use_cookies and browser:
                ydl_opts['cookiesfrombrowser'] = browser

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Find downloaded file
            video_filename = None
            for f in os.listdir(tmpdir):
                if f.endswith(('.mp4', '.mkv', '.webm')):
                    video_filename = os.path.join(tmpdir, f)
                    break

            if not video_filename:
                return None, "Downloaded video file not found."

            # Instead of loading into memory, return an open file
            video_file = open(video_filename, 'rb')
            filename = os.path.basename(video_filename)

            # Don't delete tmpdir yet — let user download first

            return video_file, filename, tmpdir  # Also return temp folder for cleanup

        except Exception as e:
            logger.error(f"yt-dlp failed with format {fmt}: {str(e)}")
            if 'Requested format is not available' in str(e) and list_formats:
                formats = get_available_formats(url, use_cookies, browser)
                return None, f"Error downloading video: {str(e)}\nAvailable formats:\n{formats}", None
            elif fmt == format_options[-1]:
                return None, f"Error downloading video: {str(e)}", None
            continue
