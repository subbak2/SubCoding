import whisper

# "C:\\Util\\ffmpeg-7.1-essentials_build\\bin\\ffmpeg.exe" 부분을 ffmpeg를 실제 압축 푼 경로로 변경해주세요
import os
os.environ["PATH"] += os.pathsep + r"C:\\Util\\ffmpeg-7.1-essentials_build\\bin"

def transcribe_audio(audio_path, output_srt):
    model = whisper.load_model("small")  # "small" "medium" "large" 순으로 정확도 상승, 시간 오래 걸림
    result = model.transcribe(audio_path, language="ko")  # 명시적으로 한국어 설정 가능
  
    # print(result)

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
