#!/usr/bin/env python3
"""
Attach Audio to Video
A script to replace the audio track in an MP4 video file with an MP3 audio file.
The video stream is copied without re-encoding for maximum speed and quality.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def attach_audio(audio_file, video_file, output_file):
    """
    Replace the audio in a video file with a new audio file.
    
    Args:
        audio_file: Path to the MP3 audio file
        video_file: Path to the input MP4 video file
        output_file: Path to the output MP4 video file
    
    Returns:
        True if successful, False otherwise
    """
    # Validate input files exist
    audio_path = Path(audio_file)
    video_path = Path(video_file)
    
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_file}", file=sys.stderr)
        return False
    
    if not video_path.exists():
        print(f"Error: Video file not found: {video_file}", file=sys.stderr)
        return False
    
    # Check if output file already exists
    output_path = Path(output_file)
    if output_path.exists():
        print(f"Error: Output file already exists: {output_file}", file=sys.stderr)
        print("Please remove it first or choose a different output filename.", file=sys.stderr)
        return False
    
    # Build ffmpeg command
    # -i video_file: input video
    # -i audio_file: input audio
    # -c:v copy: copy video stream without re-encoding
    # -c:a aac: encode audio as AAC (widely compatible)
    # -map 0:v:0: use video from first input
    # -map 1:a:0: use audio from second input
    # -shortest: finish encoding when the shortest input stream ends
    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        str(output_path)
    ]
    
    print(f"Attaching audio from '{audio_file}' to video '{video_file}'...")
    print(f"Output will be saved to '{output_file}'")
    
    try:
        # Run ffmpeg
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Successfully created '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: ffmpeg failed with exit code {e.returncode}", file=sys.stderr)
        if e.stderr:
            print(f"ffmpeg error output:\n{e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg first.", file=sys.stderr)
        print("On Ubuntu/Debian: sudo apt-get install ffmpeg", file=sys.stderr)
        print("On macOS: brew install ffmpeg", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Replace the audio in an MP4 video with an MP3 audio file.',
        epilog='Example: python attach-audio.py audio.mp3 video.mp4 video-new.mp4'
    )
    parser.add_argument('audio', help='Path to the MP3 audio file')
    parser.add_argument('video', help='Path to the input MP4 video file')
    parser.add_argument('output', help='Path to the output MP4 video file')
    
    args = parser.parse_args()
    
    success = attach_audio(args.audio, args.video, args.output)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
