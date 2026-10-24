## 주의사항
Windows의 경우 https://www.ffmpeg.org/ 에서 ffmpeg-release-essentials.zip 파일을 다운로드 받아야 합니다.

압축을 푼 뒤 `extract_audio_windows.py`의 `FFMPEG_EXE`, `generate_subtitles_windows.py`의 `FFMPEG_DIR`을 실제 경로로 바꿔 주세요.

Mac은 `brew install ffmpeg`로 설치합니다.

## 실행방법
1. Whisper 설치

   ` pip install -r requirements.txt ` (또는 ` pip install openai-whisper `)

   Mac에서 GPU로 더 빠르게 만들고 싶으면 ` pip install mlx mlx-whisper ` 도 설치합니다.

2. 비디오에서 오디오만 추출

   `extract_audio.py`의 `VIDEO_FILE`을 실제 파일 이름으로 바꾸거나, 파일 이름을 직접 넘깁니다.

   Mac의 경우, ` python ./extract_audio.py ` 또는 ` python ./extract_audio.py "내 영상.mov" `

   Windows의 경우, ` python ./extract_audio_windows.py `

3. 오디오에서 자막 추출

   Mac의 경우, ` python ./generate_subtitles.py ` (large 모델, 빠르게 하려면 ` --model small `)

   Mac에서 GPU 사용을 원하는 경우(추천), ` python ./generate_subtitles_mlx.py `

   Windows의 경우, ` python ./generate_subtitles_windows.py ` (small 모델)

결과는 `subtitles/output_korean_subtitles.srt`에 저장됩니다. 입력·출력 경로는 ` -i `, ` -o `로 바꿀 수 있습니다 (` --help `로 확인).


## 파일 설명
| 파일명                          | 설명                                                        |
|---------------------------------|-------------------------------------------------------------|
| `extract_audio.py`              | FFmpeg으로 영상에서 오디오(모노 16kHz WAV) 추출              |
| `extract_audio_windows.py`      | Windows용. ffmpeg.exe 경로만 지정하고 `extract_audio.py`를 사용 |
| `generate_subtitles.py`         | Whisper로 오디오에서 한국어 자막(SRT) 생성 (CPU·CUDA)         |
| `generate_subtitles_mlx.py`     | Apple Silicon GPU(MLX)로 자막 생성                           |
| `generate_subtitles_windows.py` | Windows용. ffmpeg 경로를 더하고 small 모델로 자막 생성         |
| `requirements.txt`              | 필요한 Python 패키지 목록                                     |
| `audio/`, `subtitles/`          | 추출한 오디오와 만들어진 자막 예시                             |


## 참고 - 약 7분 영상 자막 추출에 걸린 시간
| 모델             | M1 Max (CPU)   | M1 Max MLX (GPU)     | RTX 2070 Super (CUDA) |
|------------------|--------------|-----------------|------------------|
| Whisper Small    | 56초         | 14초            | 39초                |
| Whisper Medium   | 3분 30초     | 26초   (8bit)   | 1분 28초            |
| Whisper Large    | 5분 12초     | 39초            | 7분 10초            |
