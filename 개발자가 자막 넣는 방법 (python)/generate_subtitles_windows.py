"""Windows용 자막 생성. Whisper가 ffmpeg를 찾도록 PATH에 ffmpeg 폴더를 더하고, 기본 모델은 small.

사용법:
    python ./generate_subtitles_windows.py
    python ./generate_subtitles_windows.py --model medium
"""
import os

from generate_subtitles import parse_args, transcribe_audio

# ffmpeg를 실제로 압축 푼 경로의 bin 폴더로 바꿔주세요 (README의 주의사항 참고)
FFMPEG_DIR = r"C:\Util\ffmpeg-7.1-essentials_build\bin"


if __name__ == "__main__":
    os.environ["PATH"] += os.pathsep + FFMPEG_DIR
    args = parse_args(default_model="small")
    transcribe_audio(args.input, args.output, args.model)
    print(f"저장했습니다: {args.output}")
