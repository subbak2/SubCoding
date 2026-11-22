# 낮에 찍은 영상을 밤으로 (집 PC, ComfyUI + Wan2.1 VACE 1.3B)

섭코딩 유튜브 영상에서 쓴 설정·워크플로·프롬프트·스크립트입니다. 낮에 드론으로 찍은 논 영상을 집 PC(RTX 5070 Ti 16GB)에서 오픈소스 모델로 밤 영상으로 바꿨고, 17번 돌려서 3장면을 건졌습니다. 실패한 설정도 같이 남겼습니다.

- 영상: (발행 후 링크)
- 결과 밤 장면은 AI로 만든 상상입니다. 실제 야간 촬영이 아닙니다.

## 개발을 몰라도 됩니다

이 폴더를 통째로 받아서 **Claude Code에게 넘기고 [START_HERE.md](START_HERE.md)에 있는 한 줄을 말하면** 설치부터 실행까지 Claude가 진행합니다. 아래 내용은 Claude가 읽는 설명서이기도 합니다.

**실제로 시험해 봤습니다 (2026-11-22):** 이 저장소를 새로 clone하고, 아무 설정 없는 새 Claude Code 세션에 START_HERE의 한 줄과 영상만 줬습니다. 사람이 한 일은 ChatGPT로 밤 사진 한 장 만든 것뿐이었고, 49·81프레임 생성까지 끝났습니다 (전체 약 53분, 그중 생성 6분 18초). 단, ComfyUI와 모델이 이미 설치된 PC였고 새 PC 설치부터 검증한 것은 아닙니다.

필요한 것

| | |
|---|---|
| PC | NVIDIA 그래픽카드 (VRAM 16GB에서 확인. 12GB 이하는 시험 안 해 봄) 달린 Windows 또는 Linux 데스크탑, 여유 공간 20GB 이상 |
| Claude | [Claude Code](https://claude.com/claude-code) (유료 구독) |
| 영상 | 낮에 찍은 영상 아무거나 (하늘이 넓고 앞쪽이 단순할수록 잘 됨) |
| 이미지 AI | 첫 장면 한 장을 밤으로 바꿀 때 (ChatGPT 등, 사람이 한 번) |

## 환경 (이 영상에서 쓴 것)

| 항목 | 값 |
|---|---|
| GPU | RTX 5070 Ti 16GB (생성 중 최고 11~15.6GB 사용) |
| 실행 | ComfyUI v0.3.x 이상, 커스텀 노드 없음 (기본 노드만), Windows WSL2 Ubuntu 24.04, 127.0.0.1:8188 |
| 모델 | `wan2.1_vace_1.3B_fp16.safetensors` (4.31GB, Apache-2.0) → `ComfyUI/models/diffusion_models/` |
| 텍스트 인코더 | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (6.74GB) → `ComfyUI/models/text_encoders/` |
| VAE | `wan_2.1_vae.safetensors` (254MB) → `ComfyUI/models/vae/` |
| 받는 곳 | [Comfy-Org/Wan-2.1 (Hugging Face)](https://huggingface.co/Comfy-Org/Wan-2.1) `split_files/` 아래 |
| 스크립트 | Python 3.10 이상 + `pip install pillow`, PATH에 `ffmpeg`·`ffprobe` (`nvidia-smi`가 있으면 GPU 메모리도 기록) |

> **RTX 50 시리즈(Blackwell) + WSL2:** CUDA 12.8 이상(`cu128`) PyTorch와 이를 지원하는 Windows NVIDIA 드라이버가 필요합니다. WSL2 안에는 Linux용 NVIDIA 드라이버를 따로 설치하지 않고, ComfyUI는 `/mnt/c`가 아니라 WSL2 리눅스 폴더(`~/ComfyUI`)에 설치합니다. 메모리가 부족하면 `.wslconfig`에서 WSL 메모리를 늘립니다.

## 최종 설정 (채택 3장면 공통)

| 항목 | 값 |
|---|---|
| 해상도·길이 | 832×480, 16fps, 81프레임(약 5초) |
| 방식 | **첫 프레임 고정**: 0번 프레임 = 밤으로 바꾼 사진(mask 0), 1~80번 = 원본의 Canny 선 영상(mask 1) |
| WanVaceToVideo strength | 0.8 (채택 3장면 모두). 앞쪽이 복잡한 장면에서 0.6도 시험했지만 그 장면 본편은 불합격 |
| KSampler | seed 42, steps 20, CFG 6, uni_pc / simple, denoise 1.0 |
| ModelSamplingSD3 shift | 8 |
| 걸린 시간 | 81프레임 한 장면 약 218~240초 |

밤 첫 프레임 사진은 원본 첫 프레임을 이미지 AI로 밤 조명만 바꿔 만들었습니다 (`prompts/01_glow_night_image_edit.txt`).

## 시행착오 요약

| # | 방식 | 결과 |
|---|---|---|
| 1·2 | Canny + 밤 사진을 "참고 이미지"로만 | 실패: 밤 사진은 무시되고 Canny 선이 네온 윤곽으로 빛남 |
| 3·4 | **첫 프레임 고정** + Canny (1.0 / 0.8) | 성공: 남색 하늘·구름·별, 배치 유지. 0.8이 윤곽이 덜함 |
| 5 | 원본 영상에서 시작하는 저-denoise V2V (0.65) | 실패: 하늘이 낮 그대로 |
| 6 | 프롬프트에 반딧불이 추가 | 반딧불이는 안 생기고 달이 생김 → 반딧불이는 편집에서 합성 |
| 9~11 | 앞쪽이 복잡한 장면, strength 0.8 / 0.6 / 0.45 | 0.8 윤곽 많음, 0.6 적당, 0.45 건물이 바뀜 |
| 13~15 | 같은 장면 81프레임 본편, 네거티브·seed만 바꿔 재시도 | 전부 불합격: 49프레임 시험 성공이 81프레임 성공을 보장하지 않음 → 장면 교체 |
| 7·12·17 | 하늘이 넓은 장면 3개 본편 | **채택** |

배운 것

1. 밤 사진은 참고 이미지가 아니라 **0번 프레임으로 박아야** 색·하늘이 뒤로 번진다.
2. 화면에 선(밭이랑·덤불·건물)이 많을수록 strength를 낮춘다. 너무 낮추면 건물을 새로 지어낸다.
3. 프롬프트에 moonlight가 있으면 중간에 달이 튀어나올 수 있다.
4. 이번 반딧불이 프롬프트 시험에서는 반딧불이가 생기지 않아 편집에서 합성했다.
5. 하늘이 넓고 앞쪽이 단순한 장면을 고르는 게 설정보다 중요했다.
6. 한 번에 옵션 하나만 바꿔야 원인을 말할 수 있다.

## 파일

```
START_HERE.md                             Claude Code에게 하는 말 (여기서 시작)
workflows/first_frame_lock_api.json       성공한 방식 (ComfyUI API 형식)
workflows/drone_vace13b_canny_ref_ui.json 실패 1·2 방식 (참고 이미지, UI 형식)
workflows/drone_vace13b_smoke_ui.json     짧은 시험용 (UI 형식)
prompts/F_paddy_sky_night.txt             장면별 positive (H 능선, J 넓은 논) — 내 영상에 맞게 고쳐 쓰기
prompts/v2v_negative.txt                  네거티브 기본 (nomoon은 moon 추가판)
prompts/G_paddy_sky_fireflies.txt         반딧불이 프롬프트 (실패 기록용)
prompts/01_glow_night_image_edit.txt      첫 프레임 밤 사진을 만든 이미지 편집 프롬프트
scripts/vace_v2v.py                       ComfyUI API로 한 건 제출 + 실행 시간·GPU 기록 (마스크 생성·업로드 자동)
scripts/v2v_compare.py                    영상 준비(자르기·Canny) / 원본·결과 좌우 비교
scripts/comfy_api.py                      ComfyUI 업로드 도우미
```

## 따라 하기 (명령어)

이 폴더 최상위에서 실행합니다. ComfyUI가 `127.0.0.1:8188`에서 켜져 있어야 합니다.

1. ComfyUI(v0.3.x 이상)를 설치하고 위 모델 3개를 각 폴더에 넣은 뒤 켠다.
2. 원본에서 쓸 구간을 832×480·16fps·81프레임으로 자르고 Canny 선 영상을 만든다. `--start`는 원본에서 시작할 초.

```bash
python scripts/v2v_compare.py prepare --source original.mp4 --start 0 --out inputs --fps 16 --frames 81
```

   `inputs/`에 `reference.mp4`(잘린 원본), `control_canny.mp4`(선 영상), `first.png`(첫 장면)가 생깁니다.

3. `inputs/first.png`를 이미지 AI로 밤으로 바꿔 `inputs/night_first_frame.png`로 저장한다. 구도·건물 위치가 그대로인지 원본과 겹쳐서 확인한다 (프롬프트 예: `prompts/01_glow_night_image_edit.txt`).
4. 생성한다. 프롬프트는 내 영상 내용에 맞게 고친다.

```bash
python scripts/vace_v2v.py --name my_night \
    --control inputs/control_canny.mp4 \
    --first-frame inputs/night_first_frame.png --strength 0.8 \
    --prompt-file prompts/J_glow_sky_night.txt --negative-file prompts/v2v_negative.txt \
    --out results --compare inputs/reference.mp4
```

   `results/`에 결과 영상 경로·실행 시간·GPU 메모리(`my_night_metrics.json`)와 좌우 비교 영상이 생깁니다.

5. 처음에는 2단계를 `--frames 49 --out inputs49`로 짧게 만들어 시험하고, 괜찮으면 81프레임으로 돌린다. 생성 길이는 제어 영상의 프레임 수를 따른다. 81프레임은 따로 검수한다(49 성공이 81 성공을 보장하지 않음).

### API 그래프를 직접 쓸 때

`workflows/first_frame_lock_api.json`은 ComfyUI API 그래프입니다. 스크립트 없이 쓰려면 ComfyUI `input/`에 `control_canny.mp4`, `night_first_frame.png`, `mask.mp4`를 넣고, 그래프를 `{"prompt": 그래프}`로 감싸 `/prompt`에 POST합니다. `mask.mp4`는 832×480·16fps·81프레임이고 첫 프레임 전체가 검정, 나머지는 흰색이어야 합니다. `scripts/vace_v2v.py`는 마스크 생성과 업로드를 자동으로 합니다.

## 문제 해결

- **Windows에서 `UnicodeDecodeError`(cp949)**: 폴더 경로에 한글이 있을 때 났던 문제로, 2026-11-22에 스크립트를 UTF-8로 고정해 고쳤습니다. 예전 버전을 쓰고 있다면 최신으로 받거나 `set PYTHONUTF8=1` 뒤에 실행하세요.
- **결과가 네온 윤곽처럼 빛남**: strength를 0.8 → 0.6으로 낮춥니다. 건물이 바뀌기 시작하면 다시 올립니다.
- **중간에 달이 생김**: 네거티브를 `prompts/v2v_negative_nomoon.txt`로 바꿔 봅니다.

## 라이선스

이 폴더의 스크립트·프롬프트는 자유롭게 쓰셔도 됩니다. 모델(Wan2.1 VACE 1.3B, umt5-xxl 모두 Apache-2.0)은 각 모델의 라이선스를 따릅니다.
