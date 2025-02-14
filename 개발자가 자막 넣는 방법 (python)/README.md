## 주의사항
Windows의 경우 https://www.ffmpeg.org/ 에서 ffmpeg-release-essentials.zip 파일을 다운로드 받아야합니다.

다운로드 받은 후 압축을 풀고 path를 수정해줘야합니다.

## 실행방법
1. ` pip install openai-whisper ` 를 통해 whisper AI 를 다운받습니다.
2. 비디오에서 오디오만 추출
   
    extract_audio.py 파일에서 video_file을 실제 파일 이름으로 변경해주세요

   Mac의 경우, ` python ./extract_audio.py `

   Windows의 경우, ` python ./extract_audio_windows.py `

3. 오디오에서 자막 추출

   Mac의 경우, ` python ./generate_subtitles.py `
  
   Mac에서 pytorch 설정을 했고 GPU 사용을 원하는 경우, 

   Windows의 경우, ` python ./generate_subtitles_windows.py `


## 파일 설명
| 파일명                  | 설명                                      |
|-------------------------|-----------------------------------------|
| `extract_audio.py`      | FFmpeg을 사용해 영상에서 오디오 추출       |
| `generate_subtitles.py` | Whisper를 활용해 오디오에서 자동 자막 생성 |
| `requirements.txt`      | 필요한 Python 패키지 목록 (`ffmpeg-python`, `whisper`) |
| `README.md`            | 프로젝트 설명 및 사용법 안내              |


## 참고 - 약 7분 영상 자막 추출에 걸린 시간
| 모델             | M1 Max CPU   | M1 Max MLX      | RTX 2070 Super (CUDA) |
|------------------|--------------|-----------------|------------------|
| Whisper Small    | 56초         | 14초            | XX초            |
| Whisper Medium   | 3분 30초     | 26초   (8bit)   | XX초            |
| Whisper Large    | 5분 12초     | 39초            | XX초            |

