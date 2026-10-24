"""Apple Silicon Mac GPU(MLX)로 자막을 만든다. CPU보다 몇 배 빠르다.

설치: pip install mlx mlx-whisper
사용법:
    python ./generate_subtitles_mlx.py
    python ./generate_subtitles_mlx.py --model mlx-community/whisper-medium-mlx-8bit
모델 목록: https://huggingface.co/collections/mlx-community/whisper-663256f9964fbb1177db93dc
(whisper-large-v3-mlx, whisper-medium-mlx-8bit 추천)
"""
from generate_subtitles import LANGUAGE, parse_args, write_srt

DEFAULT_MODEL = "mlx-community/whisper-large-mlx-8bit"


def transcribe_audio(audio_path, output_srt, model=DEFAULT_MODEL):
    import mlx_whisper

    result = mlx_whisper.transcribe(str(audio_path), language=LANGUAGE, path_or_hf_repo=model)
    write_srt(result["segments"], output_srt)


if __name__ == "__main__":
    args = parse_args(default_model=DEFAULT_MODEL)
    transcribe_audio(args.input, args.output, args.model)
    print(f"저장했습니다: {args.output}")
