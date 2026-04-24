#! python3
# download youtube videos
#
# youtube -a [youtube url]
# download audio file as mp3 as well as video in mp4
#
# youtube [youtube url]
# download only video
#
# youtube -p [playlist url]
# download all videos from playlist

# list from files
# saving to different destination

#! python3
import argparse
from pathlib import Path
import yt_dlp

def main():
    # 1. Setup CLI Arguments
    parser = argparse.ArgumentParser(description="YouTube Downloader")
    parser.add_argument("urls", nargs="+", help="YouTube URLs")
    parser.add_argument("-a", "--audio", action="store_true", help="Download both MP4 and MP3")
    parser.add_argument("-p", "--playlist", action="store_true", help="Explicitly allow playlist download")
    parser.add_argument("--browser", help="Browser to take cookies from (chrome, firefox, edge)", default="chrome")
    args = parser.parse_args()

    # 2. Define Paths
    home = Path.home()
    base_dir = home / "Videos" / "YoutubeDownload"

    # 3. Configure Options
    ydl_opts = {
        # If not a playlist, it goes to root; if a playlist, it goes to a subfolder
        'outtmpl': str(base_dir / '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'retries': 3,
        # Logic: Only download playlist if -p is passed
        'noplaylist': not args.playlist,
        'extract_flat': False,        # Ensures it expands the playlist items
        'yes_playlist': args.playlist, # Forces the playlist behavior
    }

    if args.browser:
        ydl_opts['cookiesfrombrowser'] = (args.browser,)
        ydl_opts['js_runtimes'] = {'deno': {}}
        ydl_opts['remote_components'] = {'ejs:github'}
    # Adjust folder structure if it's a playlist
    if args.playlist:
        ydl_opts['outtmpl'] = str(base_dir / '%(creator)s - %(playlist_title)s' / '%(autonumber)s-%(title)s.%(ext)s')

    # 4. Handle Format & Audio Extraction
    if args.audio:
        # Download video, then keep the video and extract audio (keeping both)
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            # This is the key: it tells yt-dlp NOT to delete the video after extracting audio
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
        ydl_opts['keepvideo'] = True
    else:
        # Standard Video only
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    # 5. Execute
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in args.urls:
            print(f"🚀 Processing: {url} (Playlist: {args.playlist}, Audio: {args.audio})")
            ydl.download([url])

if __name__ == "__main__":
    main()