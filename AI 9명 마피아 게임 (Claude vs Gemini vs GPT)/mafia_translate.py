"""Optional: translate a finished game (runs/<run>/events.json) into English with one of your players.json CLIs.
Speeches, inner thoughts and vote reasons -> i18n_en.json (used by viewer/build.py --lang en) and lines_en.json (TTS).
The game itself is not changed (same meaning, natural spoken English). Animal names become English names.
Sends 30 items per call and saves after each batch, so rerunning continues where it stopped.

Usage:
  python3 mafia_translate.py --run game1 --translator sonnet          # any player key from players.json
  python3 mafia_translate.py --run game1 --translator opus --batch 20
  python3 mafia_translate.py --run test --dry-run                     # no CLI call: copies the Korean text
  Options: --out DIR (default ./runs) --config FILE (default players.json, else players.example.json)
"""
import argparse
import json
import sys
from pathlib import Path

from mafia_game import ANIMAL_EN, DEFAULT_CONFIG, DEFAULT_OUT, EXAMPLE_CONFIG, extract_json, load_players, run_command

FIELDS = ("text", "inner", "reason")


def system_text(animals):
    return ("You translate lines from a Korean Mafia party game played by AI characters into natural spoken English. "
            "Keep the exact meaning, tone, emotion and each speaker's verbal habits; do not add, soften or explain. "
            "Animal names are character names: " + ", ".join(f"{k}={v}" for k, v in animals.items()) +
            ". Game terms: 마피아=Mafia, 경찰=Detective, 의사=Doctor, 시민=Citizen, 처형=execution, 투표=vote. "
            "Use '-' not '—'. Return only JSON.")


def main():
    ap = argparse.ArgumentParser(description="Translate a Mafia game log to English (resumable)")
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--config", help="players file (default players.json, else players.example.json)")
    ap.add_argument("--translator", help="player key whose CLI does the translation (default: first player)")
    ap.add_argument("--batch", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--dry-run", action="store_true", help="no CLI call: copy the Korean text as the 'translation'")
    a = ap.parse_args()
    d = Path(a.out) / a.run
    events = json.loads((d / "events.json").read_text(encoding="utf-8"))
    cfg_path = Path(a.config) if a.config else (DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else EXAMPLE_CONFIG)
    config = load_players(cfg_path)
    translator = config[a.translator] if a.translator else next(iter(config.values()))
    # English character names: built-in table + names from the game's own setup
    animals = dict(ANIMAL_EN)
    for c, info in (events[0].get("players") or {}).items():
        if info.get("char_en"):
            animals[c] = info["char_en"]
    dst = d / "i18n_en.json"
    done = json.loads(dst.read_text(encoding="utf-8")) if dst.exists() else {}
    todo = []
    for i, e in enumerate(events):
        src = {f: e[f] for f in FIELDS if e.get(f)}
        if src and str(i) not in done:
            todo.append({"id": str(i), "speaker": animals.get(e.get("who"), e.get("who", "")), **src})
    print(f"{len(todo)} events to translate ({len(done)} already done), translator: {translator['name']}",
          file=sys.stderr)
    for s in range(0, len(todo), a.batch):
        chunk = todo[s:s + a.batch]
        prompt = (system_text(animals) + "\n\n"
                  "Translate every string field (text, inner, reason) of each item. Keep ids. "
                  'Answer as {"items": [{"id": "...", "text": "...", "inner": "...", "reason": "..."}]} '
                  "with only the fields that exist.\n\n" + json.dumps({"items": chunk}, ensure_ascii=False))
        for attempt in range(3):
            try:
                if a.dry_run:
                    raw = json.dumps({"items": [{k: v for k, v in c.items() if k != "speaker"} for c in chunk]},
                                     ensure_ascii=False)
                else:
                    raw = run_command(translator, prompt, timeout=a.timeout)
                out = extract_json(raw)
                got = {it["id"]: {f: it[f] for f in FIELDS if it.get(f)} for it in out["items"]}
                missing = [c["id"] for c in chunk if c["id"] not in got]
                if missing:
                    raise ValueError(f"missing ids {missing[:5]}")
                break
            except (RuntimeError, ValueError, KeyError) as e:
                print(f"  ! batch {s // a.batch + 1} attempt {attempt + 1}: {e}", file=sys.stderr)
        else:
            sys.exit("translation failed: run again to continue")
        done.update(got)
        dst.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(s + a.batch, len(todo))}/{len(todo)}", file=sys.stderr)
    # English lines for TTS (same format as lines.json)
    lines = json.loads((d / "lines.json").read_text(encoding="utf-8"))
    for it in lines:
        tr = done.get(str(it["event"]), {})
        it["text"] = tr.get("text") if it["type"] == "speech" else tr.get("reason", it["text"])
    (d / "lines_en.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
    print(d / "i18n_en.json", d / "lines_en.json")


if __name__ == "__main__":
    main()
