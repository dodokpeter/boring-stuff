#! python3
# convert mp4 to mp3
#
# mp4to3 [folder]

import codecs
import sys
import pathlib
from pathlib import Path

# ffmpeg on system path
# download ffmpeg: https://www.gyan.dev/ffmpeg/builds/
# https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows
import yt_dlp as youtube_dl
from audio_extract import extract_audio

# Compatibility fixes for Windows
if sys.platform == 'win32':
  # https://github.com/ytdl-org/youtube-dl/issues/820
  codecs.register(
    lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

home = str(pathlib.Path.home())

# read an options and ur
argIndex = 1
alsoAudioFile = True

joined = ' '.join(sys.argv)
fromIndex = joined.find(' ') +1
url_to_convert = joined[fromIndex:]

print("<<<" + url_to_convert + ">>>")

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

path_with_album = url_to_convert
source_dir = Path(path_with_album + '\\')
files = source_dir.glob('*.mp4')
for file in files:
    print(file.name)
    filename = file.name.replace('.mp4', '.mp3')
    audioDir = path_with_album + ' - audio\\'
    extract_audio(input_path=file, output_path=audioDir + filename)
