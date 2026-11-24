"""Game log (events.json) -> viewer data (viewer/data/<run>[_en].js, window.GAME = {...}) + sound-effect cues.
index.html loads the data with a <script> tag because fetch() is blocked on file:// pages.
Every event gets a start time and a duration, so the page can be played back or seeked frame by frame.

By default (--dual) speech/vote lengths are max(ko, en) so one video can carry a Korean and an English voice track.
The typing effect follows the screen language. --no-dual uses only the --lang length.

Input (runs/<run>/):
  events.json                      game log (required)
  result.json                      result (numbers card in the arch scene, ending)
  audio/durations.json             TTS lengths {event index: seconds} (ko). Without it: by character count
  audio_en/durations.json          English TTS lengths
  i18n_en.json                     English translation from mafia_translate.py (--lang en; missing items stay Korean)
Output:
  viewer/data/<name>.js (en: <name>_en.js)      open index.html?run=<name>&lang=en
  runs/<run>/sfx_cues.json         [{t, sfx, event}] where sound effects would go (for editing)
  runs/<run>/timeline.json         [{idx,type,start,dur,speak,who}] used by mix_audio.py
  runs/<run>/subs_ko.srt, subs_en.srt   subtitles timed like the screen
  --season: runs/season.json -> viewer/data/season.js (awards scene)

Images (optional, not included): assets/chars/<player key>.png (transparent PNG, standing character),
assets/chars_soft/<key>.png (softer version for close-ups, defaults to the same image),
assets/background.png and assets/background_blur.png (1920x1080 stage). Missing images fall back to an emoji avatar
and a plain gradient stage.

Usage (from the kit folder):
  python3 viewer/build.py --run test
  python3 viewer/build.py --run test --lang en                             # English screen
  python3 viewer/build.py --run test --from-event 1 --to-event 12 --name test_cut   # a slice (inclusive)
  python3 viewer/build.py --run test --cps 7 --pad 0.8                     # chars per second, pause after a line
  python3 viewer/build.py --season                                         # awards data from runs/season.json
  Options: --runs DIR (default ./runs, same as mafia_game.py --out)
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ASSETS = PROJECT / "assets"
RUNS = PROJECT / "runs"


def image_paths(key):
    """(img, img_soft) relative to index.html, or (None, None) when the user has not supplied a picture"""
    if not (ASSETS / "chars" / f"{key}.png").exists():
        return None, None
    img = f"../assets/chars/{key}.png"
    soft = f"../assets/chars_soft/{key}.png" if (ASSETS / "chars_soft" / f"{key}.png").exists() else img
    return img, soft


def background():
    bg = "../assets/background.png" if (ASSETS / "background.png").exists() else None
    blur = "../assets/background_blur.png" if (ASSETS / "background_blur.png").exists() else bg
    return {"bg": bg, "bg_blur": blur}


# 이벤트 종류별 고정 길이(초). speech·vote는 글자 수(또는 오디오)로 계산. index.html의 효과 타이밍과 맞춰 둔다
FIXED = {"setup": 3.0, "night": 2.8, "mafia_pick": 4.2, "doctor_save": 3.8, "police_check": 4.6,
         "death": 5.0, "no_death": 4.2, "day": 2.4, "execute": 6.6, "no_execute": 3.6, "end": 7.0}
# 효과음 큐 (이벤트 안 상대 시각, 이름) — index.html 효과와 같은 타이밍
SFX = {
    "night": [(0.0, "night_ambience")],
    "mafia_pick": [(0.0, "heartbeat"), (1.5, "stamp")],
    "doctor_save": [(0.6, "shield")],
    "police_check": [(0.4, "scan_beep"), (2.3, "stamp")],
    "death": [(0.0, "heartbeat"), (0.9, "slash"), (0.9, "impact"), (1.6, "stamp"), (1.7, "crowd_gasp")],
    "no_death": [(0.4, "shield"), (1.4, "stamp")],
    "day": [(0.0, "whoosh")],
    "speech": [(0.0, "whoosh")],
    "vote": [(0.1, "whoosh"), (0.7, "impact")],
    "execute": [(0.0, "heartbeat"), (1.9, "gavel"), (2.0, "impact"), (2.8, "crowd_gasp"), (4.0, "stamp")],
    "no_execute": [(0.3, "gavel"), (0.4, "stamp")],
    "end": [(0.0, "impact"), (0.6, "crowd_gasp")],
}
CALLOUT_SFX = [(0.0, "impact"), (0.02, "slash"), (0.15, "stamp"), (0.3, "crowd_gasp")]
CALLOUT_LEN = 1.4  # 지목당한 사람 반응샷 길이


ROLE_EN = {"마피아": "Mafia", "경찰": "Detective", "의사": "Doctor", "시민": "Citizen"}
AUDIO_PAD = 0.35  # TTS 길이 뒤 여유


def banner_text(ev, lang, name):
    """밤·처형 결과 문구 (index.html 배너와 같은 뜻). 자막용, 없으면 None"""
    ko = lang == "ko"
    t = ev["type"]
    if t == "night":
        return f"DAY {ev['day']} · 밤이 되었습니다" if ko else f"DAY {ev['day']} · Night falls"
    if t == "death":
        return f"아침… 지난밤 {name(ev['who'])}이(가) 당했다" if ko else f"Morning… {name(ev['who'])} was killed"
    if t == "no_death":
        return "아침… 아무도 죽지 않았다" if ko else "Morning… nobody died"
    if t == "execute":
        r = ev.get("role", "")
        return (f"{name(ev['who'])} 처형 ({ev.get('votes')}표) — 정체는 {r}" if ko
                else f"{name(ev['who'])} executed ({ev.get('votes')} votes) — was {ROLE_EN.get(r, r)}")
    if t == "no_execute":
        return "동률! 처형 없음" if ko else "Tie! No execution"
    if t == "end":
        w = str(ev.get("winner", ""))
        if ko:
            return f"{w} 승리" if w and "중단" not in w else w
        return "Mafia wins" if "마피아" in w else "Town wins" if "시민" in w else w
    return None


def srt_time(x):
    ms = int(round(max(0, x) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path, items):
    items = sorted((a, b, txt) for a, b, txt in items if txt and b > a)
    out = [f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n" for n, (a, b, txt) in enumerate(items, 1)]
    path.write_text("\n".join(out), encoding="utf-8")
    return len(items)


def load_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def text_dur(text, cps, pad, minimum=2.0):
    return max(minimum, len(text or "") / cps + pad)


ACCUSE = re.compile(r"의심|수상|마피아|투표|처형|거짓|이상하|모순|근거|찍|몰아|변명|suspic|sus\b|mafia|vote|lie|lying|guilty|execut|contradict|proof", re.I)
HOT_EMOTION = {"의심", "확신", "분노"}


def find_callout(text, speaker, alive, disp, emotion=""):
    """발언에서 다른 살아 있는 캐릭터를 '지목'했는지. 이름이 나오고, 그 문장에 공격적인 말이 있거나 감정이 의심·확신·분노일 때만.
    여러 명이면 가장 먼저 나온 한 명. (캐릭터, 이름 위치) 또는 None"""
    best = None
    for c in alive:
        if c == speaker:
            continue
        for m in re.finditer(re.escape(disp[c]), text, re.I):
            a = max(text.rfind(".", 0, m.start()), text.rfind("?", 0, m.start()), text.rfind("!", 0, m.start())) + 1
            ends = [i for i in (text.find(".", m.end()), text.find("?", m.end()), text.find("!", m.end())) if i != -1]
            sentence = text[a:min(ends) + 1 if ends else len(text)]
            if ACCUSE.search(sentence) or emotion in HOT_EMOTION:
                if best is None or m.start() < best[1]:
                    best = (c, m.start())
                break
    return best


def load_durations(run_dir, adir):
    d = load_json(run_dir / adir / "durations.json") or load_json(run_dir / adir / "lines_durations.json") or {}
    return {int(k): float(v) for k, v in d.items()}


def build(run, start=None, end=None, name=None, cps=None, pad=0.8, lang="ko", dual=True):
    run_dir = RUNS / run
    events = load_json(run_dir / "events.json")
    if events is None:
        sys.exit(f"{run_dir}/events.json not found")
    result = load_json(run_dir / "result.json")
    aud = {"ko": load_durations(run_dir, "audio"), "en": load_durations(run_dir, "audio_en")}
    i18n = {int(k): v for k, v in (load_json(run_dir / "i18n_en.json", {}) or {}).items()}
    CPS = {"ko": cps or 7.0, "en": 15.0} if lang == "ko" else {"ko": 7.0, "en": cps or 15.0}
    langs = ["ko", "en"] if dual else [lang]

    def tr_text(ev, key, lg):
        if lg == "ko":
            return ev.get(key) or ""
        return (i18n.get(ev["idx"]) or {}).get(key) or ev.get(key) or ""

    def length(ev, key, lg, minimum, cps_mul=1.0, pad_=None):
        """한 언어의 길이: TTS 길이(+여유)가 있으면 그것, 없으면 글자 수"""
        a = aud[lg].get(ev["idx"]) if key in ("text", "reason") else None
        if a:
            return a + AUDIO_PAD
        return text_dur(tr_text(ev, key, lg), CPS[lg] * cps_mul, pad if pad_ is None else pad_, minimum)

    setup = events[0]
    assert setup["type"] == "setup", "첫 이벤트가 setup이 아님"
    players, disp = {}, {}
    char_en = {}
    for n, (char, info) in enumerate(setup["players"].items()):
        key = info.get("key") or f"p{n + 1}"
        char_en[char] = info.get("char_en") or char
        disp[char] = char if lang == "ko" else char_en[char]
        img, soft = image_paths(key)
        players[char] = {"key": key, "model": info["model"], "company": info.get("team", "AI"),
                         "color": info.get("color", "#FFD24A"), "emoji": info.get("emoji", "🙂"),
                         "cli": info.get("cli", ""), "tagline": info.get("tagline", ""),
                         "tagline_en": info.get("tagline_en", ""), "role": info["role"],
                         "img": img, "img_soft": soft, "disp": disp[char]}
    seats = list(players)  # seat order = players.json order
    name_of = {"ko": lambda c: c, "en": lambda c: char_en.get(c, c)}

    lo = start if start is not None else 0
    hi = end if end is not None else len(events) - 1
    timeline, cues, t, alive, missing, last_callout = [], [], 0.0, set(players), 0, False
    for i, ev in enumerate(events):
        ev = dict(ev, idx=i)
        orig = dict(ev)
        if ev["type"] in ("speech", "vote", "mafia_pick", "doctor_save", "police_check") and not i18n.get(i):
            missing += 1
        if lang == "en" and i18n.get(i):
            ev.update({k: v for k, v in i18n[i].items() if k in ("text", "inner", "reason")})
        if i < lo or i > hi:
            ev["start"], ev["dur"], ev["skip"] = -1, 0, True  # 상태 계산에는 쓰고 화면에는 안 나옴
        else:
            if ev["type"] == "speech":
                type_dur = length(orig, "text", lang, 2.2)  # 타자 효과 = 화면 언어 길이
                speak = max(length(orig, "text", lg, 2.2) for lg in langs)
                inner = max(length(orig, "inner", lg, 1.8, 1.4, 0.9) for lg in langs) if ev.get("inner") else 0
                hit = find_callout(ev.get("text", ""), ev["who"], alive, disp, ev.get("emotion", ""))
                if hit and last_callout:  # 연속 지목은 건너뜀 (매번 터지면 지루함)
                    hit = None
                last_callout = bool(hit)
                if hit:
                    frac = hit[1] / max(1, len(ev.get("text", "")))
                    at = round(max(0.9, frac * type_dur * 0.82), 2)
                    ev["callout"] = {"target": hit[0], "at": at}
                    speak = max(speak, at + CALLOUT_LEN + 0.6)
                ev["speak"], ev["innerDur"], ev["typeDur"] = round(speak, 2), round(inner, 2), round(min(type_dur, speak), 2)
                d = speak + inner
            elif ev["type"] == "vote":
                last_callout = False
                d = max(max(2.2, length(orig, "reason", lg, 0, 1.6, 1.0)) for lg in langs)
            else:
                d = FIXED.get(ev["type"], 2.5)
            ev["start"], ev["dur"] = round(t, 3), round(d, 3)
            for rel, s in SFX.get(ev["type"], []):
                cues.append({"t": round(t + rel, 3), "sfx": s, "event": i})
            if ev.get("callout"):
                for rel, s in CALLOUT_SFX:
                    cues.append({"t": round(t + ev["callout"]["at"] + rel, 3), "sfx": s, "event": i})
            t += d
        if ev["type"] in ("death", "execute"):
            alive.discard(ev["who"])
        ev["_orig"] = orig
        timeline.append(ev)

    # 자막 (화면 표시 시각과 같게) + 음성 배치용 타임라인
    subs = {"ko": [], "en": []}
    for ev in timeline:
        if ev.get("skip"):
            continue
        o, st, ty = ev["_orig"], ev["start"], ev["type"]
        for lg in ("ko", "en"):
            nm = name_of[lg]
            inner_lb = "(속마음)" if lg == "ko" else "(inner thought)"
            if ty == "speech":
                subs[lg].append((st + 0.15, st + ev["speak"], f"{nm(o['who'])}: {tr_text(o, 'text', lg)}"))
                if o.get("inner"):
                    subs[lg].append((st + ev["speak"], st + ev["dur"], f"{inner_lb} {nm(o['who'])}: {tr_text(o, 'inner', lg)}"))
            elif ty == "vote":
                subs[lg].append((st + 0.1, st + ev["dur"], f"{nm(o['who'])} → {nm(o['target'])}: {tr_text(o, 'reason', lg)}"))
            elif ty in ("mafia_pick", "doctor_save", "police_check") and o.get("inner"):
                subs[lg].append((st + 1.0, st + ev["dur"], f"{inner_lb} {nm(o['who'])}: {tr_text(o, 'inner', lg)}"))
            else:
                b = banner_text(o, lg, nm)
                if b:
                    subs[lg].append((st + 0.2, st + ev["dur"], b))
    tl = [{"idx": e["idx"], "type": e["type"], "start": e["start"], "dur": e["dur"], "speak": e.get("speak"),
           "who": e.get("who")} for e in timeline if not e.get("skip")]
    for e in timeline:
        e.pop("_orig", None)
    data = {"run": run, "lang": lang, "reveal": setup.get("reveal", False), "seed": setup.get("seed"),
            "players": players, "seats": seats, "events": timeline, "total": round(t + 0.5, 3), "result": result,
            **background()}
    out = HERE / "data" / f"{name or run}{'' if lang == 'ko' else '_' + lang}.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("window.GAME = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    # 영상은 한국어 화면 하나라서 효과음 큐·타임라인·자막은 ko 빌드 기준만 쓴다 (en은 지목 위치가 달라 시각이 어긋남)
    sfx_tag = "" if not name or name == run else f"_{name}"
    cue_path = run_dir / f"sfx_cues{sfx_tag}.json"
    n_srt = None
    if lang == "ko":
        cue_path.write_text(json.dumps(sorted(cues, key=lambda c: c["t"]), ensure_ascii=False, indent=0), encoding="utf-8")
        (run_dir / f"timeline{sfx_tag}.json").write_text(json.dumps({"total": round(t + 0.5, 3), "events": tl}, ensure_ascii=False), encoding="utf-8")
        n_srt = {lg: write_srt(run_dir / f"subs{sfx_tag}_{lg}.srt", subs[lg]) for lg in ("ko", "en")}
    callouts = sum(1 for e in timeline if e.get("callout"))
    print(f"{out}  events {lo}-{hi}, {t:.1f}s, {callouts} callouts"
          + (f", {len(cues)} sfx cues -> {cue_path.name}, timeline + subtitles ko {n_srt['ko']} / en {n_srt['en']} lines" if n_srt
             else " (en screen data only; cues, timeline and subtitles come from the ko build)")
          + (" (longer of ko/en)" if dual else "")
          + (f", {missing} events without translation (shown in Korean)" if missing else ""))
    return out


def build_season():
    """runs/season.json -> viewer/data/season.js (window.SEASON)"""
    s = load_json(RUNS / "season.json")
    if not s:
        sys.exit(f"{RUNS / 'season.json'} not found: run mafia_game.py --season game1,game2,... first")
    players = {}
    for k, v in s["players"].items():
        dsp = v.get("display", {})
        img, _ = image_paths(k)
        players[k] = dict(v, key=k, company=dsp.get("team", "AI"), color=dsp.get("color", "#FFD24A"),
                          emoji=dsp.get("emoji", "🙂"), img=img, char_en=dsp.get("char_en") or v.get("char", k))
    data = {"runs": s.get("runs", []), "awards": s.get("awards", []), "ranking": s.get("ranking", []),
            "champion": s.get("champion"), "players": players, **background()}
    out = HERE / "data" / "season.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("window.SEASON = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"{out}  {len(data['awards'])} awards, champion {data['champion']}")
    return out


def main():
    ap = argparse.ArgumentParser(description="events.json -> viewer/data/<run>.js + sfx_cues.json")
    ap.add_argument("--run", help="run folder name (runs/<run>)")
    ap.add_argument("--season", action="store_true", help="runs/season.json -> data/season.js (awards scene)")
    ap.add_argument("--no-dual", action="store_true", help="use only the --lang length instead of the longer of ko/en")
    ap.add_argument("--lang", choices=["ko", "en"], default="ko")
    ap.add_argument("--from-event", type=int)
    ap.add_argument("--to-event", type=int)
    ap.add_argument("--name", help="output name (default: run name), index.html?run=<name>")
    ap.add_argument("--cps", type=float, help="characters per second (ko 7, en 15)")
    ap.add_argument("--pad", type=float, default=0.8)
    ap.add_argument("--runs", help="folder with run folders (default ./runs next to the viewer folder)")
    a = ap.parse_args()
    if a.runs:
        global RUNS
        RUNS = Path(a.runs).resolve()
    if a.season:
        build_season()
    if a.run:
        build(a.run, a.from_event, a.to_event, a.name, a.cps, a.pad, a.lang, not a.no_dual)
    elif not a.season:
        ap.error("--run or --season")


if __name__ == "__main__":
    main()
