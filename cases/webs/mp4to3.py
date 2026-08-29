#! python3
# convert mp4 to mp3
#
# mp4to3 [folder]

import argparse
import subprocess
from pathlib import Path

# ffmpeg on system path
# download ffmpeg: https://www.gyan.dev/ffmpeg/builds/
# https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows


def extract_audio(input_path, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-i", str(input_path), "-y", str(output_path)], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract mp3 audio from every .mp4 file in a folder")
    parser.add_argument("folder", nargs="+", help="folder containing .mp4 files")
    args = parser.parse_args(argv)
    folder = " ".join(args.folder)

    print(f"<<<{folder}>>>")

    source_dir = Path(folder)
    files = source_dir.glob('*.mp4')
    for file in files:
        print(file.name)
        filename = file.name.replace('.mp4', '.mp3')
        audio_dir = Path(folder + ' - audio')
        extract_audio(input_path=file, output_path=str(audio_dir / filename))


if __name__ == "__main__":
    main()
