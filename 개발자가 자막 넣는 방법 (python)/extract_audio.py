import subprocess

def extract_audio(video_path, audio_output):
    command = [
        "ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", "-ac", "1", "-ar", "16000", audio_output
    ]
    subprocess.run(command, check=True)

# 여기에 변환할 비디오 파일의 이름을 바꿔주세요 
video_file = "개발자를 위한 최고의 장난감 NAS.mov"

audio_file = "audio/extracted_audio.wav"

extract_audio(video_file, audio_file)