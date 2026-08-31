#! python3
# yt - download YouTube videos, optionally with an audio extract and/or
# transcripts. Each URL (single video or playlist) gets its own subfolder
# under the output folder, named after its title - "<content-folder>" below
# - so it stays a well-defined, self-contained thing to move (-c) without
# ever touching sibling content already sitting in the shared output folder
# (e.g. from email-extract).
#
# yt [youtube url ...]
# download only video, into <content-folder>
#
# yt -a [youtube url ...]
# also extract an mp3 into <content-folder>/audio/
#
# yt -p [youtube playlist url]
# explicitly allow playlist download (each item still lands in the same
# per-playlist <content-folder>)
#
# yt -ten -tsk [youtube url]
# also download transcripts (repeatable -t<langcode>, e.g. English +
# Slovak here) into <content-folder>, alongside the video. A language
# that isn't available is reported by yt-dlp itself and does not abort
# the rest of the download.
#
# yt -c [youtube url]
# after a successful download, move <content-folder> to
# <cloud.folder>/output - a plain local path (e.g. a Google Drive for
# Desktop mount), same pattern as shared-drive's drive.directory. No
# Google Drive API/OAuth - whatever sync client is watching that path
# picks up the move on its own.
#
# Default output folder: ~/.boring-stuff/output (same folder email-extract
# writes into).
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - only prompted for
# when -c is used:
#   cloud:
#     folder: G:\My Drive

import argparse
import shutil
import sys
from pathlib import Path

import yt_dlp

from core.configuration.user_conf import MissingConfigError, load_config_value
from core.stats import record_usage

OUTPUT_FOLDER_NAME = "output"
AUDIO_SUBFOLDER_NAME = "audio"


def validate_cloud_folder(value):
    """Raise ValueError with a clear message if `value` isn't an accessible
    directory - used to reject a bad answer before it gets persisted to
    config."""
    if not Path(value).is_dir():
        raise ValueError(f"'{value}' is not an accessible directory.")


def build_ydl_opts(output_dir, args, progress_hook):
    ydl_opts = {
        "ignoreerrors": True,
        "retries": 3,
        # Only download the single video instead of its playlist if in doubt.
        "noplaylist": not args.playlist,
        "extract_flat": False,
        "progress_hooks": [progress_hook],
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    }

    if args.playlist:
        ydl_opts["outtmpl"] = str(output_dir / "%(playlist_title,playlist)q" / "%(playlist_index)s - %(title)q.%(ext)s")
    else:
        # Give every single video its own title-named subfolder too, so
        # <content-folder> is always a real, addressable folder - never the
        # shared output root.
        ydl_opts["outtmpl"] = str(output_dir / "%(title)q" / "%(title)q.%(ext)s")

    if args.browser:
        ydl_opts["cookiesfrombrowser"] = (args.browser,)
        ydl_opts["js_runtimes"] = {"deno": {}}
        ydl_opts["remote_components"] = {"ejs:github"}

    if args.audio:
        # keepvideo=True stops FFmpegExtractAudio from deleting the source
        # video once it's pulled the mp3 out of it.
        ydl_opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
        ]
        ydl_opts["keepvideo"] = True

    if args.transcript_langs:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = args.transcript_langs
        ydl_opts["subtitlesformat"] = "srt"

    return ydl_opts


def download_one(url, output_dir, args):
    """Download a single URL (video or playlist) and return its resolved
    <content-folder> - derived from the first "finished" download's
    filename, since outtmpl templates are resolved internally by yt-dlp.
    Returns None if nothing was actually downloaded (e.g. every item in a
    playlist failed with ignoreerrors)."""
    finished_files = []

    def progress_hook(d):
        if d.get("status") == "finished":
            finished_files.append(d["filename"])

    ydl_opts = build_ydl_opts(output_dir, args, progress_hook)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not finished_files:
        return None
    return Path(finished_files[0]).parent


def move_audio_files(content_folder):
    """Move any .mp3 files sitting directly in content_folder (written next
    to the video by FFmpegExtractAudio, which has no option to redirect its
    output elsewhere) into content_folder/audio/. Returns the moved paths."""
    moved = []
    for mp3_path in content_folder.glob("*.mp3"):
        audio_dir = content_folder / AUDIO_SUBFOLDER_NAME
        audio_dir.mkdir(parents=True, exist_ok=True)
        destination = audio_dir / mp3_path.name
        shutil.move(str(mp3_path), str(destination))
        moved.append(destination)
    return moved


def move_to_cloud(content_folder, cloud_root):
    """Move content_folder (and everything under it) into
    <cloud_root>/output/<content_folder name> via a plain filesystem move -
    no Drive API/OAuth involved."""
    destination_root = cloud_root / OUTPUT_FOLDER_NAME
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / content_folder.name
    shutil.move(str(content_folder), str(destination))
    return destination


def main(argv=None):
    record_usage("yt")
    parser = argparse.ArgumentParser(description="YouTube Downloader")
    parser.add_argument("urls", nargs="+", help="YouTube URLs")
    parser.add_argument("-a", "--audio", action="store_true", help="Also extract an mp3 into <content-folder>/audio/")
    parser.add_argument("-p", "--playlist", action="store_true", help="Explicitly allow playlist download")
    parser.add_argument(
        "-t",
        "--transcript",
        dest="transcript_langs",
        action="append",
        metavar="LANGCODE",
        help="Download a transcript in this language (repeatable, e.g. -ten -tsk)",
    )
    parser.add_argument(
        "-c", "--cloud", action="store_true", help="Move the content folder to the configured cloud folder afterward"
    )
    parser.add_argument("--browser", help="Browser to take cookies from (chrome, firefox, edge)", default="chrome")
    args = parser.parse_args(argv)

    cloud_root = None
    if args.cloud:
        try:
            cloud_root = load_config_value(
                None,
                "Cloud folder root (e.g. your Google Drive mount path)",
                None,
                "cloud",
                "folder",
                validate=validate_cloud_folder,
            )
        except MissingConfigError as e:
            print(e)
            sys.exit(1)

        cloud_root = Path(cloud_root)
        if not cloud_root.is_dir():
            print(f"Configured cloud folder is not accessible: {cloud_root}")
            sys.exit(1)

    output_dir = Path.home() / ".boring-stuff" / OUTPUT_FOLDER_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    for url in args.urls:
        print(f"Processing: {url} (Playlist: {args.playlist}, Audio: {args.audio})")
        content_folder = download_one(url, output_dir, args)
        if content_folder is None:
            print(f"  Nothing was downloaded for {url}, skipping.")
            continue

        if args.audio:
            move_audio_files(content_folder)

        if args.cloud:
            destination = move_to_cloud(content_folder, cloud_root)
            print(f"  Moved to cloud: {destination}")


if __name__ == "__main__":
    main()
