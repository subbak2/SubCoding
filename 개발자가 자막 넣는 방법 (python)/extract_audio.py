"""영상에서 오디오만 뽑아 Whisper가 읽기 좋은 WAV(모노, 16kHz)로 저장한다.

사용법:
    python ./extract_audio.py                       # 아래 VIDEO_FILE을 변환
    python ./extract_audio.py "내 영상.mov"          # 파일 이름을 직접 지정
    python ./extract_audio.py "내 영상.mov" -o audio/my.wav
"""
import argparse
import subprocess
from pathlib import Path

# 여기에 변환할 비디오 파일의 이름을 바꿔주세요
VIDEO_FILE = "개발자가 자막 넣는 방법.mov"
AUDIO_FILE = "audio/extracted_audio.wav"


def extract_audio(video_path, audio_output, ffmpeg="ffmpeg"):
    """ffmpeg으로 영상의 오디오를 모노 16kHz WAV로 저장한다."""
    Path(audio_output).parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-y",           # 같은 이름 파일이 있으면 덮어쓰기
        "-i", str(video_path),
        "-map", "a",            # 오디오 트랙만
        "-ac", "1",             # 모노
        "-ar", "16000",         # 16kHz (Whisper 입력 형식)
        str(audio_output),
    ]
    subprocess.run(command, check=True)


def parse_args():
    parser = argparse.ArgumentParser(description="영상에서 오디오(WAV) 추출")
    parser.add_argument("video", nargs="?", default=VIDEO_FILE, help=f"영상 파일 (기본: {VIDEO_FILE})")
    parser.add_argument("-o", "--output", default=AUDIO_FILE, help=f"저장할 WAV 경로 (기본: {AUDIO_FILE})")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    extract_audio(args.video, args.output)
    print(f"저장했습니다: {args.output}")
