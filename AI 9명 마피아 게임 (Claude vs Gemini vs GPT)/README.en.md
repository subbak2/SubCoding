# AI Mafia (do-it-yourself kit)

[한국어](README.md)

A kit that makes AI models play the party game Mafia against each other. The moderator is one Python script (`mafia_game.py`); the players are AI CLIs you already use (`claude`, `agy` for Gemini, `codex`, ...). No human in the loop. When a game ends, `viewer/index.html` replays it as a stylized game screen.

- Night: the Mafia pick someone to eliminate, the Doctor protects someone, the Detective investigates someone.
- Day: everyone alive speaks in turn (inner thoughts are recorded separately), then votes to execute one player.
- Players only know each other by animal names, not by model (`--reveal-models` turns that off).
- The game itself is played in Korean. `mafia_translate.py` produces English subtitles and an English screen.

## Requirements

- Python 3.9+ (the game and the viewer use only the standard library)
- At least one player CLI, logged in
  - Claude Code: `claude -p`
  - Gemini: `agy -p`
  - Codex: `codex exec`
  - Any other CLI works too, as long as it takes a prompt and prints an answer: describe the command in `players.json`.
- A web browser (to watch the replay)
- Optional: `numpy` and `ffmpeg`, only for mixing voice tracks (`pip install -r requirements.txt`)

`--dry-run` works without any CLI installed.

## Watch the game from the video (no setup)

Game 1 from the video is included in `runs/game1/` (raw AI answers in `calls.json`, log in `transcript.md`).

```sh
git clone https://github.com/subbak2/SubCoding.git
cd "SubCoding/AI 9명 마피아 게임 (Claude vs Gemini vs GPT)"
python3 viewer/build.py --run game1
# open viewer/index.html?run=game1 in a browser
```

## Quickstart (no CLI calls)

```sh
python3 mafia_game.py --run test --dry-run
python3 viewer/build.py --run test
```

Then open `viewer/index.html?run=test` in a browser (drag the file into a browser window and add `?run=test` to the address). The answers are fake ("테스트 발언" = "test speech"), but you see the whole flow: night, discussion, votes, execution, victory.

Pick a scene with `&scene=`: `intro_cast` (cast intro), `game` (default), `arch` (how it works), `awards`. `&t=120` starts at 120 seconds, `&speed=2` plays at 2x, `&roles=0` hides role badges.

## A real game

1. Create the players file.
   - With all three CLIs (Claude, Gemini, Codex): `cp players.example.json players.json` (9 players)
   - With only a Claude subscription: `cp players.claude-only.example.json players.json` (5 players, different models and effort)
   - Model names change over time. Check each CLI's help and use names you actually have.
2. Run the game.

```sh
python3 mafia_game.py --run game1 --seed 11
python3 viewer/build.py --run game1
# open viewer/index.html?run=game1
```

If it stops halfway, run the same command again and it continues. Every call is saved in `runs/<run>/calls.json`, and the same `--seed` gives the same order of play. If you change the settings (players, seed, ...) but reuse a `--run` name, it stops and tells you.

### Common options

| Option | Meaning |
|---|---|
| `--config FILE` | players file (default `players.json`, else `players.example.json`) |
| `--players a,b,c,d` | only some of them play (minimum 4) |
| `--rounds N` | discussion rounds per day (default 2) |
| `--max-days N` | stop after day N (for rehearsals) |
| `--reveal-models` | everyone knows which model everyone is |
| `--mafia a,b --police c --doctor d` | fixed roles (to rotate roles fairly across games) |
| `--season game1,game2,game3` | points over several games + 9 awards -> `runs/season.json` |
| `--summary` | print the saved result |

Roles: with 9 players, Mafia 2, Detective 1, Doctor 1, Citizen 5. Otherwise Mafia 1 (up to 6 players) or 2 (7+), Detective 1, Doctor 1, the rest Citizens.

### players.json format

```json
{"players": [
  {"key": "opus", "name": "Claude Opus 5.5", "character": "부엉이", "character_en": "Owl", "team": "Claude",
   "cmd": ["claude", "-p", "--model", "opus", "--output-format", "text", "--tools", "", "--effort", "medium"]}
]}
```

- `key` short id, `name` model name shown on screen, `character` in-game name (an animal, in Korean since the game is in Korean; must be unique)
- `cmd` is the command as an argv list. Placeholders:
  - `{prompt}`: the prompt is passed as this argument; without it the prompt goes to stdin.
  - `{output_file}`: the answer is read from this file; without it, from stdout.
  - `{timeout}`: replaced by the time limit in seconds (default 300).
- Optional: `character_en` (English name; common animals are built in), `emoji`, `team` (grouping on the intro screen), `color`, `tagline`/`tagline_en`, `prompt_suffix` (text appended to the prompt), `timeout`, `timeout_grace` (extra seconds to wait after the CLI's own limit)

## Output files (`runs/<run>/`)

| File | Contents |
|---|---|
| `transcript.md` | human-readable log (speeches, inner thoughts, votes, night actions) |
| `result.json` | winner, roles, survival, vote accuracy, points, call count, response time per model |
| `events.json` | event list for the viewer |
| `lines.json` | lines for TTS (speeches and vote reasons) |
| `calls.json` | call cache (raw answer, seconds, failure reason) |
| `meta.json` | settings of this run (checked when continuing) |

Points: winning team +3, survived +1, +1 per vote on a Mafia, Mafia never executed +2. For the awards scene run `python3 mafia_game.py --season game1,game2,game3`, then `python3 viewer/build.py --season`.

## Replay screen (`viewer/`)

- `build.py` turns `events.json` into timed screen data (`viewer/data/<run>.js`). It also writes subtitles (`subs_ko.srt`, `subs_en.srt`), sound-effect cue times (`sfx_cues.json`) and `timeline.json` for voice placement.
- English screen: `python3 mafia_translate.py --run game1 --translator sonnet` (translates with one of your players' CLIs) -> `python3 viewer/build.py --run game1 --lang en` -> `index.html?run=game1&lang=en`
- The nine characters and the stage from the video (AI-generated) are in `assets/`, named after each player `key` in `players.json`. Delete them and the viewer draws emoji avatars and a plain stage. To use your own:
  - `assets/chars/<key>.png` standing character (transparent PNG, portrait)
  - `assets/chars_soft/<key>.png` softer version for close-ups (defaults to the same picture)
  - `assets/background.png`, `assets/background_blur.png` 1920x1080 stage (the 9-player layout assumes 9 chairs in a row)
- Making a video: screen recording is the simplest. For frame-exact output, open `index.html?run=game1&render=1` in a headless browser, call `window.seek(seconds)` per frame and capture. `window.sceneInfo()` lists the scenes and their lengths.
- Voice (optional): read `lines.json` with any TTS into `runs/<run>/audio/<event index>.wav`, write the lengths to `audio/durations.json` (`{"event index": seconds}`) and rerun `build.py` so the screen follows the audio. `python3 viewer/mix_audio.py --run game1` mixes them into one track (`--bgm`, `--sfx` optional).

## Fairness

- Every player gets the same prompt format: rules, player list, private info only they see, public log, the current task, a JSON answer format.
- Each call runs in a fresh empty temp directory with no tools, so no project files or earlier conversations leak in.
- No fallback model. If the answer is not valid JSON or names someone not on the list, the same model is asked twice more; after that the action is recorded as an abstention (`failed_calls` in `result.json`).
- Roles and seats come from the seed. Over several games, rotate roles with `--mafia/--police/--doctor`.
- A handful of games is not a ranking of model ability: luck, seats and roles matter a lot.

## Cost and limits

One game makes roughly 50-75 CLI calls (9 players, 3-5 days). On a subscription plan that uses a good share of usage limits (such as 5-hour windows); on API-billed CLIs it costs accordingly. Try `--dry-run` first, then a short `--max-days 1`, then the real game. A game usually takes 10-15 minutes.

## License

MIT (`LICENSE`), covering the code and the pictures in `assets/`.
