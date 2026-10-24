"""Windows용 오디오 추출. ffmpeg.exe 위치만 다르고 나머지는 extract_audio.py와 같다.

사용법:
    python ./extract_audio_windows.py
    python ./extract_audio_windows.py "내 영상.mov" -o audio/my.wav
"""
from extract_audio import extract_audio, parse_args

# ffmpeg를 실제로 압축 푼 경로로 바꿔주세요 (README의 주의사항 참고)
FFMPEG_EXE = r"C:\Util\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"


if __name__ == "__main__":
    args = parse_args()
    extract_audio(args.video, args.output, ffmpeg=FFMPEG_EXE)
    print(f"저장했습니다: {args.output}")
