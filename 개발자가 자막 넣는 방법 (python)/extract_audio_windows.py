import subprocess

# "C:\\Util\\ffmpeg-7.1-essentials_build\\bin\\ffmpeg.exe" 부분을 ffmpeg를 실제 압축 푼 경로로 변경해주세요
def extract_audio(video_path, audio_output):
    command = [
        "C:\\Util\\ffmpeg-7.1-essentials_build\\bin\\ffmpeg.exe", "-i", video_path, "-q:a", "0", "-map", "a", "-ac", "1", "-ar", "16000", audio_output
    ]
    subprocess.run(command, check=True)

# 여기에 변환할 비디오 파일의 이름을 바꿔주세요 
video_file = "개발자를 위한 최고의 장난감 NAS.mov"

audio_file = "aduio/extracted_audio.wav"

extract_audio(video_file, audio_file)