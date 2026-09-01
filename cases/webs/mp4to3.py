#! python3
# mp4to3 - extract mp3 audio from an .mp4 file, or every .mp4 file in a
# folder, into a sibling "<name> - audio" folder.
#
# mp4to3 <file.mp4>   extract just that one file's audio
# mp4to3 <folder>     extract audio from every .mp4 file in the folder

import argparse
import subprocess
from pathlib import Path

from core.stats import record_usage

# ffmpeg on system path
# download ffmpeg: https://www.gyan.dev/ffmpeg/builds/
# https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows


def extract_audio(input_path, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-i", str(input_path), "-y", str(output_path)], check=True)


def main(argv=None):
    record_usage("mp4to3")
    parser = argparse.ArgumentParser(description="Extract mp3 audio from an .mp4 file, or every .mp4 file in a folder")
    parser.add_argument("path", nargs="+", help="an .mp4 file, or a folder containing .mp4 files")
    args = parser.parse_args(argv)
    path = Path(" ".join(args.path))

    if not path.exists():
        print(f"'{path}' does not exist.")
        return

    if path.is_file():
        audio_dir = Path(f"{path.parent} - audio")
        extract_audio(input_path=path, output_path=str(audio_dir / path.name.replace(".mp4", ".mp3")))
        return

    print(f"<<<{path}>>>")
    audio_dir = Path(f"{path} - audio")
    for file in path.glob("*.mp4"):
        print(file.name)
        filename = file.name.replace(".mp4", ".mp3")
        extract_audio(input_path=file, output_path=str(audio_dir / filename))


if __name__ == "__main__":
    main()
