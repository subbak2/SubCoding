"""오디오에서 한국어 자막(SRT)을 만든다. OpenAI Whisper, CPU(또는 CUDA) 사용.

사용법:
    python ./generate_subtitles.py                      # large 모델
    python ./generate_subtitles.py --model small        # 빠르게 (small < medium < large 순으로 정확, 느림)
    python ./generate_subtitles.py -i audio/my.wav -o subtitles/my.srt
"""
import argparse
from pathlib import Path

AUDIO_FILE = "audio/extracted_audio.wav"
OUTPUT_SRT = "subtitles/output_korean_subtitles.srt"
LANGUAGE = "ko"


def format_time(seconds):
    """초를 SRT 시간 형식(00:01:02,345)으로 바꾼다."""
    total_ms = int(round(seconds * 1000))
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(segments, output_srt):
    """Whisper 결과의 segments를 SRT 파일로 저장한다."""
    Path(output_srt).parent.mkdir(parents=True, exist_ok=True)
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time(segment['start'])} --> {format_time(segment['end'])}\n")
            f.write(f"{segment['text'].strip()}\n\n")


def transcribe_audio(audio_path, output_srt, model_name="large"):
    import whisper  # pip install openai-whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), language=LANGUAGE)
    write_srt(result["segments"], output_srt)


def parse_args(default_model):
    parser = argparse.ArgumentParser(description="오디오에서 한국어 자막(SRT) 만들기")
    parser.add_argument("-i", "--input", default=AUDIO_FILE, help=f"오디오 파일 (기본: {AUDIO_FILE})")
    parser.add_argument("-o", "--output", default=OUTPUT_SRT, help=f"저장할 SRT (기본: {OUTPUT_SRT})")
    parser.add_argument("--model", default=default_model, help=f"Whisper 모델 (기본: {default_model})")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args(default_model="large")
    transcribe_audio(args.input, args.output, args.model)
    print(f"저장했습니다: {args.output}")
