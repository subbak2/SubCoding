import mlx_whisper
# pip install mlx mlx-whisper

def transcribe_audio(audio_path, output_srt):
    result = mlx_whisper.transcribe(audio_path, language="ko", path_or_hf_repo="mlx-community/whisper-medium-mlx-8bit")  # whisper-large-v3-mlx, whisper-medium-mlx-8bit 추천
    # model 목록 참고 https://huggingface.co/collections/mlx-community/whisper-663256f9964fbb1177db93dc
  
    print(result)

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]

            f.write(f"{i+1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

audio_file = "audio/extracted_audio.wav"
output_srt = "subtitles/output_korean_subtitles.srt"
transcribe_audio(audio_file, output_srt)
