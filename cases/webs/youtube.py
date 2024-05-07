#! python3
# download youtube videos
#
# youtube -a [youtube url]
# a means also download audio file as mp3
#
# youtube [youtube url]
# download only video
#
# youtube [playlist url]
# download all videos from playlist

# list from files
# saving to different destination


import codecs
import sys
import os
import pathlib
from pathlib import Path

# https://stackoverflow.com/a/75504772 when ERROR: Unable to extract uploader id; please report this issue on https://yt-dl.org/bug
# pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz

# ffmpeg on system path
# download ffmpeg: https://www.gyan.dev/ffmpeg/builds/
# https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows
import yt_dlp as youtube_dl
from audio_extract import extract_audio

# Examples for lib
# https://www.programcreek.com/python/example/98358/youtube_dl.YoutubeDL

MP3 = '.mp3'
EXT = 'ext'
PLAYLIST_TITLE = 'playlist_title'
CREATOR = 'creator'
TITLE = 'title'
PLAYLIST_INDEX = 'playlist_index'
ENTRIES = 'entries'
PLAYLIST = 'playlist'
TYPE = '_type'

# Compatibility fixes for Windows
if sys.platform == 'win32':
    # https://github.com/ytdl-org/youtube-dl/issues/820
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

home = str(pathlib.Path.home())

# read an options and ur
argIndex = 1
alsoAudioFile = False

if str(sys.argv[1]).startswith('-a'):
    argIndex += 1
    alsoAudioFile = True

url_to_download = sys.argv[argIndex:]

# download video
# make it more sofisticated and configurable
dir = home + '\\Videos\\YoutubeDownload\\'
albumFolder = '%(creator)s - %(playlist_title)s\\'
mp3albumFolder = '%(creator)s - %(playlist_title)s - audio\\'
outtmpl = dir + albumFolder + '%(autonumber)s-%(title)s.%(ext)s'
retries = 3
cachedir = home + '\\Videos\\cacheYoutube\\'
verbose = None
format = 'mp4'

ydl_opts = { #https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L128-L278
    'forceformat': format,
    'format': format,
    'outtmpl': outtmpl,
    'retries': retries,
    'logtostderr': outtmpl == '-',
    'verbose': verbose,
    'cachedir': cachedir,
    'ignoreerrors': True,
#      'writesubtitles": True,
#      'writeautomaticsub': 'true',
#         allsubtitles:      Downloads all the subtitles of the video
#                            (requires writesubtitles or writeautomaticsub)
#         listsubtitles:     Lists all available subtitles for the video
#         subtitlesformat:   The format code for subtitles
#      'subtitleslangs': 'en,ge,sk,cz',
}


def mp3(mp3_file_name, mp4_file, audioDir = dir + 'audio\\'):
    if alsoAudioFile:
        print('             MP3 Video ' + mp4_file)
        print('             MP3 Audio ' + audioDir + mp3_file_name + MP3)
        if not os.path.exists(audioDir):
            pathlib.Path(audioDir).mkdir(parents=True, exist_ok=True)

        extract_audio(input_path=mp4_file, output_path = audioDir + mp3_file_name + MP3)

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url_to_download[0], download=True)
    if TYPE in info.keys() and info[TYPE] == PLAYLIST and alsoAudioFile:

        # if creator is not present, then youtube dl use NA string
        creator = 'NA' #video[CREATOR]
        if creator is None: creator = 'NA'

        path_with_album = dir + creator + ' - ' + info[TITLE]
        source_dir = Path(path_with_album)
        files = source_dir.glob('*.mp4')

        for file in files:
            filename = file.name.replace('.mp4', MP3)
            audioDir = path_with_album + ' - audio\\'
            extract_audio(input_path=file, output_path = audioDir + filename)
    else:
        mp3(info.get(TITLE), ydl.prepare_filename(info))

