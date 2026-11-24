"""Optional: place per-line voice wavs on the video timeline -> one voice track per language (wav, 48kHz).
Sound effects and background music are optional. Needs numpy and ffmpeg (ffmpeg reads any audio format).

Input (runs/<run>/):
  timeline.json                written by viewer/build.py (ko build) {total, events:[{idx,type,start,dur,speak,who}]}
  audio/<event index>.wav      Korean TTS (--lang ko) / audio_en/<event index>.wav English TTS (--lang en)
                               (make them from lines.json / lines_en.json with any TTS you like)
  sfx_cues.json                sound-effect cues [{t, sfx, event}] (only with --sfx DIR)
Output: runs/<run>/mix_<lang>.wav (16-bit 48kHz, mono by default)

Usage (from the kit folder):
  python3 viewer/mix_audio.py --run game1 --lang ko
  ... --lang en --sfx sfx/              # files named <cue name>*.wav (e.g. whoosh_1.wav) at cue times, -6dB
  ... --bgm bgm.wav --bgm-gain -20 --duck 8   # loop music, 8dB lower while someone speaks
  ... --bgm-dir bgm/                          # per-phase music (file names containing day/night/vote/award)
  ... --sfx-gain -9 --voice-gain 0 --out mix.wav --stereo --runs DIR
Voice start: speech = event start +0.15s (after the close-up zoom), vote reason = +0.1s. Warns if a line is longer than its slot.
After adding TTS, put durations in runs/<run>/audio/durations.json ({event index: seconds}) and rerun build.py
so the slots match the audio.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
RUNS = PROJECT / "runs"
SR = 48000
VOICE_OFFSET = {"speech": 0.15, "vote": 0.1}


def decode(path, sr=SR):
    """ffmpeg로 mono float32 배열"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"디코딩 실패 {path}: {r.stderr.decode()[-200:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def db(x):
    return 10 ** (x / 20)


def place(track, clip, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(track) or i + len(clip) <= 0:
        return 0
    a, b = max(0, i), min(len(track), i + len(clip))
    track[a:b] += clip[a - i:b - i] * gain
    return b - a


def write_wav(path, x, stereo=False):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype("<i2")
    if stereo:
        pcm = np.repeat(pcm[:, None], 2, axis=1).reshape(-1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def smooth_mask(intervals, n, ramp=0.25):
    """대사 구간 1, 나머지 0, 앞뒤 ramp초로 부드럽게 (BGM 덕킹용)"""
    m = np.zeros(n, dtype=np.float32)
    for a, b in intervals:
        m[max(0, int(a * SR)):min(n, int(b * SR))] = 1
    k = max(1, int(ramp * SR))
    kernel = np.ones(k, dtype=np.float32) / k
    return np.clip(np.convolve(m, kernel, mode="same") * 1.0, 0, 1)


def pick_sfx(files_by_name, name, key):
    files = files_by_name.get(name)
    if not files:
        return None
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return files[h % len(files)]  # 같은 큐는 항상 같은 파일 (재실행해도 같은 결과)


# 장면별 BGM: 이벤트 종류 → 곡 (--bgm-dir 안 파일 이름에 이 단어가 들어 있으면 그 곡)
PHASE_OF = {"night": "night", "mafia_pick": "night", "doctor_save": "night", "police_check": "night",
            "death": "night", "no_death": "night", "setup": "day", "day": "day", "speech": "day",
            "vote": "vote", "execute": "vote", "end": "award"}


def phase_bgm(tl, bgm_dir, n, xfade=1.5):
    """이벤트 종류에 따라 낮·밤·투표·시상 곡을 바꿔 깐다. 곡마다 절대 시각 기준 루프, 경계는 xfade초 크로스페이드"""
    files = {}
    for f in sorted(Path(bgm_dir).expanduser().glob("*")):
        if f.suffix.lower() in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
            for ph in set(PHASE_OF.values()):
                if ph in f.stem.lower():
                    files.setdefault(ph, f)
    spans = {}
    for e in tl["events"]:
        ph = PHASE_OF.get(e["type"], "day")
        if ph not in files:
            ph = "day" if "day" in files else next(iter(files), None)
        if ph:
            spans.setdefault(ph, []).append((e["start"], e["start"] + e["dur"]))
    masks = {ph: smooth_mask(iv, n, ramp=xfade) for ph, iv in spans.items()}
    total = np.maximum(sum(masks.values()), 1e-6)
    bed = np.zeros(n, dtype=np.float32)
    for ph, m in masks.items():
        b = decode(files[ph])
        b = b / max(1e-6, float(np.sqrt(np.mean(b ** 2))))  # 곡끼리 음량 맞춤 (RMS 1 기준, 실제 크기는 --bgm-gain)
        bed += np.tile(b, int(np.ceil(n / len(b))))[:n] * (m / total)
    return bed, "장면별 " + ", ".join(f"{ph}={files[ph].name}" for ph in spans)


def mix(run, lang="ko", sfx_dir=None, sfx_gain=-6.0, bgm=None, bgm_gain=-20.0, duck=8.0, voice_gain=0.0,
        out=None, stereo=False, timeline_name="timeline.json", bgm_dir=None):
    run_dir = RUNS / run
    tl_path = run_dir / timeline_name
    if not tl_path.exists():
        sys.exit(f"{tl_path} not found: run viewer/build.py --run {run} first (ko build)")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    n = int((tl["total"] + 1.0) * SR)
    voice = np.zeros(n, dtype=np.float32)
    adir = run_dir / ("audio" if lang == "ko" else "audio_en")
    placed, missing, overrun, spans = 0, 0, [], []
    for e in tl["events"]:
        if e["type"] not in VOICE_OFFSET:
            continue
        f = adir / f"{e['idx']}.wav"
        if not f.exists():
            missing += 1
            continue
        clip = decode(f)
        t0 = e["start"] + VOICE_OFFSET[e["type"]]
        slot = (e.get("speak") or e["dur"]) - VOICE_OFFSET[e["type"]] if e["type"] == "speech" else e["dur"] - VOICE_OFFSET[e["type"]]
        if len(clip) / SR > slot + 0.05:
            overrun.append((e["idx"], round(len(clip) / SR, 2), round(slot, 2)))
        place(voice, clip, t0, db(voice_gain))
        spans.append((t0, t0 + len(clip) / SR))
        placed += 1
    track = voice.copy()
    n_sfx = 0
    if sfx_dir:
        cues_path = run_dir / "sfx_cues.json"
        cues = json.loads(cues_path.read_text(encoding="utf-8")) if cues_path.exists() else []
        files = {}
        for f in sorted(Path(sfx_dir).expanduser().glob("*")):
            if f.suffix.lower() in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
                # crowd_gasp_1, crowd_gasp_261123_234608 → crowd_gasp (끝의 숫자 묶음을 뗀다)
                files.setdefault(re.sub(r"(_\d+)+$", "", f.stem).lower(), []).append(f)
        cache, unknown = {}, set()
        for i, c in enumerate(cues):
            f = pick_sfx(files, c["sfx"].lower(), f"{c['sfx']}:{c['event']}:{i}")
            if not f:
                unknown.add(c["sfx"])
                continue
            if f not in cache:
                cache[f] = decode(f)
            place(track, cache[f], c["t"], db(sfx_gain))
            n_sfx += 1
        if unknown:
            print(f"  no file for sound effect (skipped): {', '.join(sorted(unknown))}")
    bgm_note = ""
    if bgm or bgm_dir:
        env = db(bgm_gain) * (1 - (1 - db(-duck)) * smooth_mask(spans, n))
        if bgm_dir:
            bed, bgm_note = phase_bgm(tl, bgm_dir, n)
        else:
            b = decode(bgm)
            bed = np.tile(b, int(np.ceil(n / len(b))))[:n] if len(b) else np.zeros(n, dtype=np.float32)
            bgm_note = Path(bgm).name
        track += bed * env
    peak = float(np.max(np.abs(track))) if len(track) else 0
    if peak > 0.98:
        track *= 0.98 / peak
        print(f"  peak {peak:.2f} -> lowered to 0.98")
    out = Path(out) if out else run_dir / f"mix_{lang}.wav"
    write_wav(out, track, stereo)
    print(f"{out}  {tl['total']:.1f}s, {placed} lines placed ({missing} without wav), {n_sfx} sound effects"
          + (f", BGM {bgm_note}" if bgm_note else ""))
    for idx, ln, slot in overrun[:10]:
        print(f"  ! event {idx}: line {ln}s > slot {slot}s (rerun build.py after writing audio/durations.json)")
    return out


def main():
    ap = argparse.ArgumentParser(description="Place line wavs on the timeline -> one voice track per language")
    ap.add_argument("--run", required=True)
    ap.add_argument("--lang", choices=["ko", "en"], default="ko")
    ap.add_argument("--sfx", help="sound-effect folder (<name>*.wav, e.g. whoosh_1.wav)")
    ap.add_argument("--sfx-gain", type=float, default=-6.0, help="sound-effect gain dB (default -6)")
    ap.add_argument("--bgm", help="background music file (looped)")
    ap.add_argument("--bgm-dir", help="per-phase music folder: files whose names contain day/night/vote/award (instead of --bgm)")
    ap.add_argument("--bgm-gain", type=float, default=-20.0, help="music gain dB (default -20)")
    ap.add_argument("--duck", type=float, default=8.0, help="dB to lower music while someone speaks (default 8)")
    ap.add_argument("--voice-gain", type=float, default=0.0)
    ap.add_argument("--timeline", default="timeline.json", help="timeline file in runs/<run>/ (slice builds: timeline_<name>.json)")
    ap.add_argument("--stereo", action="store_true", help="2 identical channels instead of mono")
    ap.add_argument("--out")
    ap.add_argument("--runs", help="folder with run folders (default ./runs)")
    a = ap.parse_args()
    if a.runs:
        global RUNS
        RUNS = Path(a.runs).resolve()
    mix(a.run, a.lang, a.sfx, a.sfx_gain, a.bgm, a.bgm_gain, a.duck, a.voice_gain, a.out, a.stereo, a.timeline, a.bgm_dir)


if __name__ == "__main__":
    main()
