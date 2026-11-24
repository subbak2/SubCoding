# AI 마피아 (직접 해 보기 키트)

[English](README.en.md)

AI 모델끼리 마피아 게임을 하게 만드는 키트입니다. 사회자는 파이썬 스크립트 하나(`mafia_game.py`)이고, 플레이어는 이미 쓰고 있는 AI CLI(`claude`, `agy`(Gemini), `codex` 등)입니다. 사람은 개입하지 않습니다. 게임이 끝나면 `viewer/index.html`로 게임 화면처럼 다시 볼 수 있습니다.

- 밤: 마피아가 한 명을 고르고, 의사가 한 명을 지키고, 경찰이 한 명을 조사합니다.
- 낮: 살아 있는 사람이 돌아가며 말하고(속마음은 따로 기록), 투표로 한 명을 처형합니다.
- 플레이어는 동물 이름으로만 불리고, 누가 어떤 모델인지 모릅니다(`--reveal-models`로 공개 가능).
- 게임 진행은 한국어입니다. 영어 자막·화면은 `mafia_translate.py`로 번역해서 만듭니다.

## 필요한 것

- Python 3.9 이상 (게임과 뷰어는 표준 라이브러리만 씀)
- 플레이어로 쓸 CLI 중 하나 이상, 로그인된 상태로
  - Claude Code: `claude -p`
  - Gemini: `agy -p`
  - Codex: `codex exec`
  - 다른 CLI도 됩니다. 프롬프트를 받아 답을 텍스트로 내놓기만 하면 `players.json`에 명령을 적어 쓸 수 있습니다.
- 브라우저 (리플레이 보기)
- 선택: 음성 트랙을 합칠 때만 `numpy`와 `ffmpeg` (`pip install -r requirements.txt`)

`--dry-run`은 CLI가 하나도 없어도 돌아갑니다.

## 영상 속 게임 그대로 보기 (설치 없음)

영상 1판 기록이 `runs/game1/`에 들어 있습니다 (AI 답 원문 `calls.json`, 진행 기록 `transcript.md` 포함).

```sh
git clone https://github.com/subbak2/SubCoding.git
cd "SubCoding/AI 9명 마피아 게임 (Claude vs Gemini vs GPT)"
python3 viewer/build.py --run game1
# 브라우저로 viewer/index.html?run=game1
```

## 빠르게 해 보기 (CLI 호출 없음)

```sh
python3 mafia_game.py --run test --dry-run
python3 viewer/build.py --run test
```

그다음 브라우저로 `viewer/index.html?run=test`를 엽니다 (파일을 브라우저에 끌어다 놓고 주소 끝에 `?run=test`를 붙여도 됩니다). 답은 "테스트 발언" 같은 가짜지만 밤, 토론, 투표, 처형, 승리까지 흐름이 다 보입니다.

장면은 `&scene=`로 고릅니다: `intro_cast`(참가자 소개), `game`(기본), `arch`(구조 설명), `awards`(시상식). `&t=120`은 120초부터, `&speed=2`는 2배속, `&roles=0`은 역할 배지를 숨깁니다.

## 실제 게임

1. 참가자 파일을 만듭니다.
   - CLI 세 개(Claude·Gemini·Codex)가 다 있으면: `cp players.example.json players.json` (9명)
   - Claude 구독 하나만 있으면: `cp players.claude-only.example.json players.json` (5명, 모델과 effort를 다르게)
   - 모델 이름은 계속 바뀝니다. 각 CLI의 도움말에서 지금 쓸 수 있는 이름으로 고치세요.
2. 게임을 돌립니다.

```sh
python3 mafia_game.py --run game1 --seed 11
python3 viewer/build.py --run game1
# 브라우저로 viewer/index.html?run=game1
```

중간에 끊겨도 같은 명령을 다시 실행하면 이어서 합니다. 모든 호출은 `runs/<run>/calls.json`에 저장되고, 같은 `--seed`면 같은 순서로 진행됩니다. 설정(참가자·seed 등)을 바꾸고 같은 `--run` 이름을 쓰면 멈추고 알려 줍니다.

### 자주 쓰는 옵션

| 옵션 | 뜻 |
|---|---|
| `--config FILE` | 참가자 파일 (기본 `players.json`, 없으면 `players.example.json`) |
| `--players a,b,c,d` | 일부만 참가 (최소 4명) |
| `--rounds N` | 하루 토론 바퀴 수 (기본 2) |
| `--max-days N` | N일차까지만 (리허설용) |
| `--reveal-models` | 서로 어떤 모델인지 알고 시작 |
| `--mafia a,b --police c --doctor d` | 역할을 정해서 시작 (여러 판에 걸쳐 역할을 공평하게 돌릴 때) |
| `--season game1,game2,game3` | 여러 판 점수 합산과 상 9개 → `runs/season.json` |
| `--summary` | 저장된 결과만 출력 |

역할 수: 9명이면 마피아 2, 경찰 1, 의사 1, 시민 5. 그 외에는 6명 이하 마피아 1, 7명 이상 마피아 2, 경찰 1, 의사 1, 나머지 시민.

### players.json 형식

```json
{"players": [
  {"key": "opus", "name": "Claude Opus 5.5", "character": "부엉이", "team": "Claude",
   "cmd": ["claude", "-p", "--model", "opus", "--output-format", "text", "--tools", "", "--effort", "medium"]}
]}
```

- `key` 영문 id, `name` 화면에 나올 모델 이름, `character` 게임 안 이름(동물, 서로 달라야 함)
- `cmd`는 실행할 명령(argv 목록). 자리표시자:
  - `{prompt}`가 있으면 프롬프트를 그 인자로 넘기고, 없으면 표준 입력으로 넘깁니다.
  - `{output_file}`이 있으면 답을 그 파일에서 읽고, 없으면 표준 출력에서 읽습니다.
  - `{timeout}`은 초 단위 제한 시간(기본 300)으로 바뀝니다.
- 선택: `character_en`(영어 이름), `emoji`, `team`(소개 화면 묶음), `color`, `tagline`/`tagline_en`(소개 한 줄), `prompt_suffix`(프롬프트 끝에 붙일 말), `timeout`, `timeout_grace`(CLI 자체 제한 뒤 더 기다릴 초)

## 결과 파일 (`runs/<run>/`)

| 파일 | 내용 |
|---|---|
| `transcript.md` | 사람이 읽는 기록 (발언, 속마음, 투표, 밤 행동) |
| `result.json` | 승패, 역할, 생존, 투표 적중, 점수, 호출 수, 모델별 응답 시간 |
| `events.json` | 뷰어용 이벤트 목록 |
| `lines.json` | TTS용 대사 목록 (발언과 투표 이유) |
| `calls.json` | 호출 캐시 (원문 답, 걸린 초, 실패 이유) |
| `meta.json` | 이 실행의 설정 (이어 하기 확인용) |

점수: 이긴 팀 +3, 끝까지 생존 +1, 마피아에게 한 투표마다 +1, 마피아인데 처형 안 당함 +2. 시상식 데이터는 `python3 mafia_game.py --season game1,game2,game3` 다음 `python3 viewer/build.py --season`.

## 리플레이 화면 (`viewer/`)

- `build.py`: `events.json`을 시간표가 있는 화면 데이터(`viewer/data/<run>.js`)로 바꿉니다. 자막 `subs_ko.srt`·`subs_en.srt`, 효과음 위치 `sfx_cues.json`, 음성 배치용 `timeline.json`도 같이 만듭니다.
- 영어 화면: `python3 mafia_translate.py --run game1 --translator sonnet` (참가자 중 하나의 CLI로 번역) → `python3 viewer/build.py --run game1 --lang en` → `index.html?run=game1&lang=en`
- 영상에 나온 캐릭터 9명·무대 그림(AI 이미지 생성)이 `assets/`에 들어 있습니다. 파일 이름은 `players.json`의 `key`와 같습니다. 그림을 지우면 동물 이모지 원과 기본 무대로 그립니다. 바꾸려면:
  - `assets/chars/<key>.png` 서 있는 캐릭터 (투명 배경 PNG, 세로로 긴 그림)
  - `assets/chars_soft/<key>.png` 클로즈업 때 쓸 부드러운 버전 (없으면 같은 그림)
  - `assets/background.png`, `assets/background_blur.png` 1920×1080 무대 (9명 자리 배치는 가로로 놓인 의자 9개 기준)
- 영상으로 만들기: 화면 녹화가 가장 간단합니다. 프레임 단위로 뽑고 싶으면 `index.html?run=game1&render=1`을 헤드리스 브라우저로 열고 프레임마다 `window.seek(초)`를 부른 뒤 캡처하세요. `window.sceneInfo()`가 장면별 길이를 알려 줍니다.
- 음성(선택): `lines.json`을 원하는 TTS로 읽혀 `runs/<run>/audio/<이벤트 번호>.wav`로 두고, 길이를 `audio/durations.json`(`{"이벤트 번호": 초}`)에 적은 뒤 `build.py`를 다시 돌리면 화면이 음성 길이에 맞춰집니다. `python3 viewer/mix_audio.py --run game1`이 한 트랙으로 합칩니다 (`--bgm`, `--sfx` 선택).

## 공정하게 하려고 한 것

- 모든 플레이어가 같은 형식의 프롬프트를 받습니다: 규칙, 참가자 목록, 자기만 보는 비밀 정보, 공개 기록, 지금 할 일, JSON 답 형식.
- 호출마다 새 빈 임시 폴더에서 도구 없이 실행합니다. 작업 폴더의 설정 파일이나 이전 대화가 끼어들지 않습니다.
- 대체 모델이 없습니다. 답이 JSON이 아니거나 대상이 목록에 없으면 같은 모델에 2번 더 묻고, 그래도 안 되면 그 행동은 기권으로 기록합니다 (`result.json`의 `failed_calls`).
- 역할과 자리는 seed로 정합니다. 여러 판을 할 때는 `--mafia/--police/--doctor`로 역할을 돌려 주세요.
- 몇 판만으로는 모델 실력 순위가 아닙니다. 운과 자리, 역할의 영향이 큽니다.

## 비용과 한도

한 판에 CLI 호출이 대략 50~75번 나갑니다 (9명, 3~5일). 구독 요금제라면 5시간 한도 같은 사용량 제한을 꽤 씁니다. API 키로 과금되는 CLI라면 그만큼 비용이 나갑니다. 먼저 `--dry-run`, 다음에 `--max-days 1`로 짧게 확인하고 본게임을 돌리세요. 한 판은 보통 10~15분 걸립니다.

## 라이선스

MIT (`LICENSE`). 코드와 `assets/` 그림 모두 자유롭게 쓰셔도 됩니다.
