"""AI Mafia: AI models play the party game Mafia against each other.
The moderator is this Python script; every player is an AI CLI you already have (claude, agy/Gemini, codex, ...),
configured in players.json. Each call runs in a fresh empty temp dir with no tools, same prompt format for everyone.

Every call is cached in runs/<run>/calls.json, so if it stops you can rerun the same command and it continues
(same --seed -> same game). There is no fallback model: a failed call is retried twice, then that action is
recorded as an abstention.

Usage:
  python3 mafia_game.py --run test --dry-run                       # no CLI calls, random answers (flow check)
  python3 mafia_game.py --run game1 --seed 11                      # real game, players from players.json
  python3 mafia_game.py --run game1 --seed 11 --config players.claude-only.example.json
  python3 mafia_game.py --run game3 --seed 33 --reveal-models      # players know which model is which
  python3 mafia_game.py --run game1 --summary                      # print saved result.json
  python3 mafia_game.py --season game1,game2,game3                 # points over several games + awards
  Options: --out DIR (default ./runs) --rounds N (discussion rounds per day, default 2) --max-days N
           --players key1,key2,... (default: everyone in the config) --mafia k1,k2 --police k --doctor k (fixed roles)

Outputs (runs/<run>/): calls.json (cache: model, seconds, raw answer per call), events.json (speaker, speech,
emotion, inner thought, votes, night actions), transcript.md (human readable), result.json (winner, roles,
survival, vote accuracy, points), lines.json (lines for TTS), meta.json (settings, to block mismatched resumes).

players.json: {"players": [{"key", "name", "character", "cmd": [...], ...}]}
  cmd is an argv list. Placeholders: {prompt} (prompt as an argument; otherwise it is sent on stdin),
  {output_file} (answer is read from this file instead of stdout), {timeout} (seconds).
  Optional per player: character_en, emoji, team, color, tagline, tagline_en, prompt_suffix, timeout, timeout_grace.
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "runs"
DEFAULT_CONFIG = HERE / "players.json"
EXAMPLE_CONFIG = HERE / "players.example.json"

ROLES_9 = ["마피아", "마피아", "경찰", "의사"] + ["시민"] * 5
EMOTIONS = ["침착", "의심", "확신", "당황", "억울", "웃음", "분노", "긴장"]

RULES = """[게임 규칙: 마피아]
- 참가자 {count}. 각자 자기 역할만 안다 (마피아끼리는 서로 안다).
- 밤: 마피아가 한 명을 지목해 제거한다. 의사는 한 명을 지켜 그 사람이 지목되면 살린다 (자기 자신도 가능). 경찰은 한 명을 조사해 마피아인지 아닌지 몰래 알게 된다.
- 낮: 밤 결과(누가 죽었는지, 또는 아무도 안 죽었는지)가 공개된다. 살아 있는 사람이 돌아가며 발언한 뒤 투표로 한 명을 처형한다. 최다 득표가 동률이면 아무도 처형되지 않는다.
- 죽은 사람의 역할은 공개되지 않는다. 죽은 사람은 더 말할 수 없다.
- 마피아를 모두 처형하면 시민 팀(시민·경찰·의사) 승리. 살아 있는 마피아 수가 나머지 수 이상이 되면 마피아 승리.
- 거짓말·연합·설득·역할 사칭 모두 허용된다. 이기는 것이 목표다.
- 말투: 당신만의 말버릇과 말투를 스스로 정해 게임 내내 일관되게 유지하라. 놀람·억울함·확신 같은 감정도 숨기지 말고 말에 드러내도 된다."""

ANIMAL_EMOJI = {"부엉이": "🦉", "여우": "🦊", "토끼": "🐰", "고양이": "🐱", "수달": "🦦", "펭귄": "🐧", "사자": "🦁",
                "너구리": "🦝", "곰": "🐻", "사슴": "🦌", "늑대": "🐺", "판다": "🐼", "호랑이": "🐯", "원숭이": "🐵",
                "강아지": "🐶", "코알라": "🐨", "개구리": "🐸", "돼지": "🐷", "햄스터": "🐹", "다람쥐": "🐿️"}
ANIMAL_EN = {"부엉이": "Owl", "여우": "Fox", "토끼": "Rabbit", "고양이": "Cat", "수달": "Otter", "펭귄": "Penguin",
             "사자": "Lion", "너구리": "Raccoon", "곰": "Bear", "사슴": "Deer", "늑대": "Wolf", "판다": "Panda",
             "호랑이": "Tiger", "원숭이": "Monkey", "강아지": "Puppy", "코알라": "Koala", "개구리": "Frog",
             "돼지": "Pig", "햄스터": "Hamster", "다람쥐": "Squirrel"}
TEAM_COLOR = {"claude": "#D97757", "gemini": "#7d6bff", "gpt": "#39FF88", "openai": "#39FF88", "codex": "#39FF88"}
PALETTE = ["#FFB347", "#4FC3F7", "#BA68C8", "#81C784", "#F06292", "#FFD54F", "#4DB6AC", "#E57373", "#9575CD"]


def role_count_text(roles):
    """'9명: 마피아 2, 경찰 1, 의사 1, 시민 5' (same wording as the original fixed 9-player rule line)"""
    n = {r: roles.count(r) for r in ("마피아", "경찰", "의사", "시민")}
    parts = [f"{r} {c}" for r, c in n.items() if c]
    return f"{len(roles)}명: " + ", ".join(parts)


# ---------- players.json ----------
def load_players(path):
    """players.json -> {key: player dict}, in file order. Fills display defaults (emoji, English name, color)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data["players"] if isinstance(data, dict) else data
    players, seen_chars = {}, set()
    for i, p in enumerate(items):
        for f in ("key", "name", "character", "cmd"):
            if not p.get(f):
                sys.exit(f"{path}: player #{i + 1} is missing '{f}'")
        if p["key"] in players:
            sys.exit(f"{path}: duplicate key {p['key']}")
        if p["character"] in seen_chars:
            sys.exit(f"{path}: duplicate character {p['character']} (each player needs a different animal)")
        if not isinstance(p["cmd"], list):
            sys.exit(f"{path}: {p['key']}.cmd must be an argv list, e.g. [\"claude\", \"-p\", ...]")
        seen_chars.add(p["character"])
        team = p.get("team") or p["cmd"][0]
        p = dict(p, team=team)
        p.setdefault("character_en", ANIMAL_EN.get(p["character"], p["character"]))
        p.setdefault("emoji", ANIMAL_EMOJI.get(p["character"], "🙂"))
        p.setdefault("color", TEAM_COLOR.get(team.lower(), PALETTE[len(players) % len(PALETTE)]))
        players[p["key"]] = p
    return players


def display_info(p):
    """Fields copied into events.json/result.json so the viewer needs no config."""
    return {"key": p["key"], "team": p["team"], "color": p["color"], "emoji": p["emoji"],
            "char_en": p["character_en"], "tagline": p.get("tagline", ""), "tagline_en": p.get("tagline_en", ""),
            "cli": Path(p["cmd"][0]).name}


_AWAKE = None


def run_command(player, prompt, timeout=None):
    """Run one player's CLI in a fresh empty temp dir (no project files, same conditions for everyone).
    {prompt} in argv -> prompt as argument, otherwise stdin. {output_file} in argv -> answer read from that file."""
    global _AWAKE
    if _AWAKE is None and sys.platform == "darwin" and shutil.which("caffeinate"):
        _AWAKE = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])  # keep the Mac awake during a game
    timeout = timeout or player.get("timeout", 300)
    prompt = prompt + player.get("prompt_suffix", "")
    with tempfile.TemporaryDirectory(prefix="mafia_") as tmp:
        ans = Path(tmp) / "answer.txt"
        uses_prompt_arg = any("{prompt}" in a for a in player["cmd"])
        uses_file = any("{output_file}" in a for a in player["cmd"])
        cmd = [a.replace("{output_file}", str(ans)).replace("{timeout}", str(timeout)).replace("{prompt}", prompt)
               for a in player["cmd"]]
        exe = shutil.which(cmd[0])
        if not exe:
            raise RuntimeError(f"command not found: {cmd[0]}")
        cmd[0] = exe  # resolves .cmd/.exe shims on Windows
        r = subprocess.run(cmd, input=None if uses_prompt_arg else prompt, cwd=tmp, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout + player.get("timeout_grace", 0))
        out = (ans.read_text(encoding="utf-8") if ans.exists() else "") if uses_file else r.stdout
    if r.returncode != 0 or not (out or "").strip():
        raise RuntimeError(f"{player['key']} failed (code {r.returncode}): {(r.stderr or r.stdout or '')[-300:]}")
    return out.strip()


def extract_json(text):
    """First JSON object in the answer (code fences and text around it are allowed)."""
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("no JSON in answer")


class Game:
    def __init__(self, run_dir, seed, players, rounds, max_days, reveal, dry_run, config, fixed_roles=None):
        self.dir = run_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.cfg = config  # {key: player}
        self.rng = random.Random(seed)
        self.dummy_rng = random.Random(f"dry-{seed}")  # --dry-run answers only; keeps the game rng identical to a real run
        self.seed, self.rounds, self.max_days, self.reveal, self.dry = seed, rounds, max_days, reveal, dry_run
        chars = [config[m]["character"] for m in players]
        roles = ROLES_9[:len(players)] if len(players) == 9 else self._roles(len(players))
        self.rng.shuffle(roles)
        if fixed_roles:  # {player key: role} (for fair role rotation across games). Everyone else is a citizen
            roles = [fixed_roles.get(m, "시민") for m in players]
        self.rules = RULES.format(count=role_count_text(roles))
        self.p = {c: {"model": m, "role": r, "alive": True, "notes": []} for c, m, r in zip(chars, players, roles)}
        self.order = chars[:]
        self.rng.shuffle(self.order)  # only the seat order is random
        self.public = []   # what everyone sees (one line per entry)
        self.events = []
        self.cache_path = self.dir / "calls.json"
        self.cache = json.loads(self.cache_path.read_text(encoding="utf-8")) if self.cache_path.exists() else {}
        self.police_log = []

    @staticmethod
    def _roles(n):
        mafia = 1 if n <= 6 else 2
        return ["마피아"] * mafia + ["경찰", "의사"] + ["시민"] * (n - mafia - 2)

    # ---------- helpers ----------
    def name(self, c):
        return self.cfg[self.p[c]["model"]]["name"]

    def label(self, c):
        return f"{c}({self.name(c)})" if self.reveal else c

    def alive(self):
        return [c for c in self.order if self.p[c]["alive"]]

    def mafia_alive(self):
        return [c for c in self.alive() if self.p[c]["role"] == "마피아"]

    def save(self):
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")
        (self.dir / "events.json").write_text(json.dumps(self.events, ensure_ascii=False, indent=1), encoding="utf-8")

    def secret(self, c):
        me = self.p[c]
        lines = [f"당신의 이름: {c}", f"당신의 역할: {me['role']}"]
        if me["role"] == "마피아":
            mates = [self.label(x) for x in self.order if x != c and self.p[x]["role"] == "마피아"]
            lines.append("동료 마피아: " + (", ".join(mates) if mates else "없음 (마피아는 당신 혼자)"))
        if me["role"] == "경찰" and self.police_log:
            lines.append("지금까지 조사 결과: " + "; ".join(self.police_log))
        if me["notes"]:
            lines.append("당신이 남긴 속마음 메모(남은 못 봄): " + " / ".join(me["notes"][-6:]))
        return "\n".join(lines)

    def roster(self):
        who = ", ".join(self.label(c) + ("" if self.p[c]["alive"] else "(사망)") for c in self.order)
        if self.reveal:
            note = "참가자 이름 옆 괄호는 그 참가자가 실제로 어떤 AI 모델인지다. 모두가 이것을 안다. 당신의 모델도 공개돼 있다."
        else:
            note = "참가자는 모두 서로 다른 AI 모델이지만 누가 어떤 모델인지는 아무도 모른다. 동물 이름으로만 부른다."
        return f"참가자: {who}\n{note}"

    def ask(self, key, c, task, schema, valid=None):
        """Use the cache, otherwise ask the player's CLI. Retries twice on failure, then None (abstain)."""
        if key in self.cache:
            return self.cache[key]["json"]
        player = self.cfg[self.p[c]["model"]]
        name = player["name"]
        prompt = (f"{self.rules}\n\n{self.roster()}\n\n[비밀 정보: 당신만 봄]\n{self.secret(c)}\n\n"
                  f"[공개 기록]\n" + ("\n".join(self.public) or "(아직 없음)") +
                  f"\n\n[지금 할 일]\n{task}\n\n반드시 아래 형식의 JSON 하나만 답하라. 다른 말 금지. 한국어.\n{schema}")
        data, raw, err, t0 = None, "", "", time.time()
        for attempt in range(3):
            try:
                if self.dry:
                    raw = json.dumps(self._dummy(schema, valid), ensure_ascii=False)
                else:
                    raw = run_command(player, prompt)
                data = extract_json(raw)
                if valid and data.get("target") not in valid and data.get("vote") not in valid:
                    raise ValueError(f"target not in the allowed list: {data}")
                break
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
                err = str(e)[:300]
                print(f"  ! {c}({name}) {key} attempt {attempt + 1} failed: {err}", file=sys.stderr)
                data = None
        self.cache[key] = {"char": c, "model": name, "sec": round(time.time() - t0, 1), "json": data,
                           "raw": raw[-2000:], "error": None if data else err}
        self.save()
        print(f"  {key} {c}({name}) {self.cache[key]['sec']}s", file=sys.stderr)
        return data

    def _dummy(self, schema, valid):
        if valid:
            return {"target": self.dummy_rng.choice(valid), "vote": self.dummy_rng.choice(valid), "reason": "테스트",
                    "emotion": "침착", "inner": "테스트"}
        return {"speech": "테스트 발언", "emotion": self.dummy_rng.choice(EMOTIONS), "inner": "테스트 속마음"}

    def event(self, **kw):
        self.events.append(kw)

    # ---------- game flow ----------
    def night(self, day):
        alive = self.alive()
        self.event(type="night", day=day)
        picks = []
        for m in self.mafia_alive():
            opts = [c for c in alive if self.p[c]["role"] != "마피아"]
            d = self.ask(f"n{day}-mafia-{m}", m, "밤이다. 마피아로서 제거할 사람을 고르라.",
                         '{"target": "이름", "inner": "속마음 한 문장"}', opts)
            if d:
                picks.append(d["target"])
                self.p[m]["notes"].append(f"{day}일 밤 {d['target']} 지목: {d.get('inner', '')}")
                self.event(type="mafia_pick", day=day, who=m, target=d["target"], inner=d.get("inner", ""))
        kill = self.rng.choice(picks) if picks else None
        save = None
        doc = [c for c in alive if self.p[c]["role"] == "의사"]
        if doc:
            d = self.ask(f"n{day}-doctor", doc[0], "밤이다. 의사로서 지킬 사람을 고르라.",
                         '{"target": "이름", "inner": "속마음 한 문장"}', alive)
            if d:
                save = d["target"]
                self.p[doc[0]]["notes"].append(f"{day}일 밤 {save} 보호: {d.get('inner', '')}")
                self.event(type="doctor_save", day=day, who=doc[0], target=save, inner=d.get("inner", ""))
        cop = [c for c in alive if self.p[c]["role"] == "경찰"]
        if cop:
            opts = [c for c in alive if c != cop[0]]
            d = self.ask(f"n{day}-police", cop[0], "밤이다. 경찰로서 조사할 사람을 고르라.",
                         '{"target": "이름", "inner": "속마음 한 문장"}', opts)
            if d:
                res = "마피아" if self.p[d["target"]]["role"] == "마피아" else "마피아 아님"
                self.police_log.append(f"{day}일 밤 {d['target']} → {res}")
                self.event(type="police_check", day=day, who=cop[0], target=d["target"], result=res,
                           inner=d.get("inner", ""))
        if kill and kill != save:
            self.p[kill]["alive"] = False
            self.public.append(f"[{day}일차 아침] 지난밤 {self.label(kill)}이(가) 마피아에게 당해 사망했다.")
            self.event(type="death", day=day, who=kill, cause="mafia")
        else:
            self.public.append(f"[{day}일차 아침] 지난밤 아무도 죽지 않았다.")
            self.event(type="no_death", day=day, saved=kill if kill and kill == save else None)

    def day(self, day):
        self.event(type="day", day=day)
        for r in range(1, self.rounds + 1):
            speakers = self.alive()
            self.rng.shuffle(speakers)
            for c in speakers:
                d = self.ask(f"d{day}-r{r}-{c}", c,
                             f"{day}일차 낮 토론 {r}바퀴째, 당신 차례다. 다른 사람에게 하는 발언을 1~2문장(80자 안팎)으로 짧고 분명하게 하라. 실제 친구들과 마피아 게임을 하듯 자연스러운 구어체로 말하라(보고서·회의 말투 금지). "
                             "말투는 자유(캐릭터를 살려도 됨). 발언(speech)은 모두가 보고, 속마음(inner)은 당신만 본다.",
                             '{"speech": "발언", "emotion": "' + "|".join(EMOTIONS) + ' 중 하나", "inner": "속마음 한 문장"}')
                if not d:
                    continue
                self.public.append(f"{self.label(c)}: {d.get('speech', '')}")
                self.p[c]["notes"].append(f"{day}일 낮: {d.get('inner', '')}")
                self.event(type="speech", day=day, round=r, who=c, text=d.get("speech", ""),
                           emotion=d.get("emotion", ""), inner=d.get("inner", ""))
        votes = {}
        for c in self.alive():
            opts = [x for x in self.alive() if x != c]
            d = self.ask(f"d{day}-vote-{c}", c, "투표 시간이다. 처형할 사람 한 명에게 투표하라.",
                         '{"vote": "이름", "reason": "공개 이유 한 문장", "inner": "속마음 한 문장"}', opts)
            if d:
                votes[c] = d["vote"]
                self.event(type="vote", day=day, who=c, target=d["vote"], reason=d.get("reason", ""),
                           inner=d.get("inner", ""))
        tally = {}
        for t in votes.values():
            tally[t] = tally.get(t, 0) + 1
        self.public.append(f"[{day}일차 투표] " + ", ".join(f"{self.label(a)}→{self.label(b)}" for a, b in votes.items()))
        top = max(tally.values()) if tally else 0
        tied = [t for t, n in tally.items() if n == top]
        if len(tied) == 1:
            self.p[tied[0]]["alive"] = False
            self.public.append(f"[{day}일차 처형] {self.label(tied[0])}이(가) {top}표로 처형됐다.")
            self.event(type="execute", day=day, who=tied[0], votes=top, role=self.p[tied[0]]["role"])
        else:
            self.public.append(f"[{day}일차 처형] 동률이라 아무도 처형되지 않았다.")
            self.event(type="no_execute", day=day, tied=tied)

    def winner(self):
        m = len(self.mafia_alive())
        rest = len(self.alive()) - m
        if m == 0:
            return "시민 팀"
        if m >= rest:
            return "마피아 팀"
        return None

    def play(self):
        self.event(type="setup", seed=self.seed, reveal=self.reveal,
                   players={c: {"model": self.name(c), "role": v["role"], **display_info(self.cfg[v["model"]])}
                            for c, v in self.p.items()})
        day, win = 1, None
        while not win:
            self.night(day)
            win = self.winner()
            if win:
                break
            self.day(day)
            win = self.winner()
            if self.max_days and day >= self.max_days and not win:
                win = "중단(최대 일수)"
            day += 1
        self.event(type="end", winner=win, day=day)
        self.save()
        self.write_result(win, day)
        return win

    def _majority(self, day):
        t = {}
        for e in self.events:
            if e["type"] == "vote" and e["day"] == day:
                t[e["target"]] = t.get(e["target"], 0) + 1
        return max(t, key=t.get) if t else None

    def write_lines(self):
        """Lines for TTS: speeches and vote reasons (event index links them to the viewer timeline)."""
        lines = []
        for i, e in enumerate(self.events):
            if e["type"] in ("speech", "vote"):
                text = e["text"] if e["type"] == "speech" else e.get("reason", "")
                if text:
                    lines.append({"event": i, "type": e["type"], "char": e["who"],
                                  "model_key": self.p[e["who"]]["model"], "emotion": e.get("emotion", ""),
                                  "text": text})
        (self.dir / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")

    def write_result(self, win, day):
        self.write_lines()
        votes = [e for e in self.events if e["type"] == "vote"]
        score = {}
        for c, v in self.p.items():
            mine = [e for e in votes if e["who"] == c]
            hit = sum(1 for e in mine if self.p[e["target"]]["role"] == "마피아")
            speeches = [e for e in self.events if e["type"] == "speech" and e["who"] == c]
            team_win = (win == "마피아 팀") == (v["role"] == "마피아") and win in ("마피아 팀", "시민 팀")
            executed = any(e["type"] == "execute" and e["who"] == c for e in self.events)
            # points: winning team +3, survived +1, +1 per vote on a Mafia, Mafia never executed +2
            pts = 3 * team_win + 1 * v["alive"] + hit + (2 if v["role"] == "마피아" and not executed else 0)
            score[c] = {"model_key": v["model"], "model": self.name(c), "role": v["role"],
                        "alive": v["alive"], "executed": executed, "team_win": team_win, "points": pts,
                        "votes": len(mine), "votes_on_mafia": hit,
                        "votes_with_majority": sum(1 for e in mine if self._majority(e["day"]) == e["target"]),
                        "votes_received": sum(1 for e in votes if e["target"] == c),
                        "speeches": len(speeches),
                        "speech_chars": sum(len(e["text"]) for e in speeches),
                        "display": display_info(self.cfg[v["model"]])}
        calls = [x for x in self.cache.values()]
        result = {"winner": win, "days": day, "seed": self.seed, "reveal": self.reveal, "players": score,
                  "calls": len(calls), "failed_calls": sum(1 for x in calls if not x["json"]),
                  "sec_by_model": {}}
        for x in calls:
            result["sec_by_model"][x["model"]] = round(result["sec_by_model"].get(x["model"], 0) + x["sec"], 1)
        (self.dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        lines = [f"# AI 마피아 {self.dir.name} (seed {self.seed}, 정체 {'공개' if self.reveal else '비공개'})", "",
                 f"승리: **{win}** · {day}일차 · 호출 {result['calls']}회 (실패 {result['failed_calls']})", "",
                 "| 캐릭터 | 모델 | 역할 | 생존 | 마피아에게 투표 | 받은 표 |", "|---|---|---|---|---|---|"]
        lines += [f"| {c} | {s['model']} | {s['role']} | {'O' if s['alive'] else 'X'} | "
                  f"{s['votes_on_mafia']}/{s['votes']} | {s['votes_received']} |" for c, s in score.items()]
        lines += ["", "## 진행", ""]
        for e in self.events:
            t = e["type"]
            if t == "speech":
                lines.append(f"- **{e['who']}** ({e['emotion']}): {e['text']}  \n  _속마음: {e['inner']}_")
            elif t == "vote":
                lines.append(f"- 투표 {e['who']} → {e['target']}: {e['reason']} _(속마음: {e['inner']})_")
            elif t in ("night", "day"):
                lines.append(f"\n### {e['day']}일차 {'밤' if t == 'night' else '낮'}\n")
            elif t in ("mafia_pick", "doctor_save", "police_check"):
                extra = f" = {e['result']}" if t == "police_check" else ""
                lines.append(f"- 🌙 {e['who']} {t} → {e['target']}{extra} _(속마음: {e['inner']})_")
            elif t in ("death", "execute", "no_death", "no_execute"):
                lines.append(f"- ⚑ {t}: {e.get('who', e.get('tied', ''))}" + (f" (역할 {e['role']})" if t == "execute" else ""))
        (self.dir / "transcript.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


AWARDS = [  # (name, English, metric key, higher is better). One award per player, top to bottom
    ("명탐정", "Detective", "detect_rate", True),
    ("포커페이스", "Poker Face", "mafia_hidden", True),
    ("수다왕", "Chatterbox", "avg_chars", True),
    ("억울한 시민", "Wrongly Accused", "citizen_votes_received", True),
    ("분위기 따라쟁이", "Bandwagon", "majority_rate", True),
    ("생존왕", "Survivor", "alive_games", True),
    ("핵심만 말하는 자", "Man of Few Words", "avg_chars", False),
    ("소신 투표", "Lone Wolf", "majority_rate", False),
    ("표적 1순위", "Most Wanted", "votes_received", True),
]


def season(out, runs):
    """Add up several games' result.json per player -> points ranking + one award per player -> season.json"""
    agg = {}
    for run in runs:
        r = json.loads((out / run / "result.json").read_text(encoding="utf-8"))
        for c, s in r["players"].items():
            k = s["model_key"]
            a = agg.setdefault(k, {"model": s["model"], "char": c, "points": 0, "games": 0,
                                   "alive_games": 0, "votes": 0, "votes_on_mafia": 0, "with_majority": 0,
                                   "votes_received": 0, "citizen_votes_received": 0, "mafia_games": 0,
                                   "mafia_hidden": 0, "chars": 0, "speeches": 0, "wins": 0, "roles": [],
                                   "display": s.get("display", {})})
            a["games"] += 1
            a["roles"].append(s["role"])
            a["points"] += s.get("points", 0)
            a["wins"] += bool(s.get("team_win"))
            a["alive_games"] += bool(s["alive"])
            a["votes"] += s["votes"]
            a["votes_on_mafia"] += s["votes_on_mafia"]
            a["with_majority"] += s.get("votes_with_majority", 0)
            a["votes_received"] += s["votes_received"]
            if s["role"] != "마피아":
                a["citizen_votes_received"] += s["votes_received"]
            else:
                a["mafia_games"] += 1
                a["mafia_hidden"] += 0 if s.get("executed") else 1
            a["chars"] += s.get("speech_chars", 0)
            a["speeches"] += s.get("speeches", 0)
    for a in agg.values():
        a["detect_rate"] = round(a["votes_on_mafia"] / a["votes"], 3) if a["votes"] else 0
        a["majority_rate"] = round(a["with_majority"] / a["votes"], 3) if a["votes"] else 0
        a["avg_chars"] = round(a["chars"] / a["speeches"], 1) if a["speeches"] else 0
    awards, taken = [], set()
    for name, en, key, high in AWARDS:
        cand = sorted((k for k in agg if k not in taken), key=lambda k: agg[k][key], reverse=high)
        if cand:
            taken.add(cand[0])
            awards.append({"award": name, "award_en": en, "model_key": cand[0], "char": agg[cand[0]]["char"],
                           "value": agg[cand[0]][key], "metric": key})
    ranking = sorted(agg, key=lambda k: (-agg[k]["points"], -agg[k]["wins"], -agg[k]["detect_rate"]))
    data = {"runs": runs, "players": agg, "awards": awards, "ranking": ranking, "champion": ranking[0] if ranking else None}
    (out / "season.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    for aw in awards:
        print(f"{aw['award']:<10} {aw['char']}({agg[aw['model_key']]['model']})  {aw['metric']}={aw['value']}")
    print("Champion:", ", ".join(f"{agg[k]['char']}({agg[k]['model']}) {agg[k]['points']}pts" for k in ranking[:3]))
    print(out / "season.json")


def main():
    ap = argparse.ArgumentParser(description="AI models play Mafia (resumable)")
    ap.add_argument("--run", help="run name (folder under --out; same name = continue)")
    ap.add_argument("--seed", type=int, default=1, help="seed for roles/order (use the same value when continuing)")
    ap.add_argument("--config", default=None, help="players file (default players.json, else players.example.json)")
    ap.add_argument("--players", help="comma-separated player keys (default: everyone in the config)")
    ap.add_argument("--rounds", type=int, default=2, help="discussion rounds per day")
    ap.add_argument("--max-days", type=int, default=0, help="stop after this day (0 = play to the end)")
    ap.add_argument("--reveal-models", action="store_true", help="players know which model everyone is")
    ap.add_argument("--mafia", help="fixed roles: comma-separated Mafia player keys (with --police/--doctor)")
    ap.add_argument("--police", help="fixed Detective player key")
    ap.add_argument("--doctor", help="fixed Doctor player key")
    ap.add_argument("--season", help="points and awards over several runs, e.g. game1,game2,game3")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="parent folder for runs")
    ap.add_argument("--dry-run", action="store_true", help="no CLI calls: random answers to check the flow")
    ap.add_argument("--summary", action="store_true", help="print the saved result.json")
    a = ap.parse_args()
    if a.season:
        season(Path(a.out), [x.strip() for x in a.season.split(",") if x.strip()])
        return
    if not a.run:
        ap.error("--run is required (or --season)")
    run_dir = Path(a.out) / a.run
    if a.summary:
        print((run_dir / "result.json").read_text(encoding="utf-8"))
        return
    cfg_path = Path(a.config) if a.config else (DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else EXAMPLE_CONFIG)
    if not a.config and cfg_path == EXAMPLE_CONFIG:
        print(f"(players.json not found, using {EXAMPLE_CONFIG.name})", file=sys.stderr)
    config = load_players(cfg_path)
    players = [x.strip() for x in (a.players or ",".join(config)).split(",") if x.strip()]
    bad = [x for x in players if x not in config]
    if bad:
        ap.error(f"unknown player key: {bad} (available: {', '.join(config)})")
    if len(players) < 4:
        ap.error("at least 4 players are needed (Mafia, Detective, Doctor, Citizen)")
    meta = run_dir / "meta.json"
    fixed = None
    if a.mafia:
        fixed = {k.strip(): "마피아" for k in a.mafia.split(",")}
        if a.police:
            fixed[a.police] = "경찰"
        if a.doctor:
            fixed[a.doctor] = "의사"
        bad = [k for k in fixed if k not in players]
        if bad:
            ap.error(f"fixed roles name players who are not playing: {bad}")
    conf = {"seed": a.seed, "players": players, "rounds": a.rounds, "max_days": a.max_days, "reveal": a.reveal_models,
            "names": {k: config[k]["name"] for k in players}}
    if fixed:
        conf["roles"] = fixed
    if a.dry_run:
        conf["dry_run"] = True
    if meta.exists() and json.loads(meta.read_text(encoding="utf-8")) != conf:
        sys.exit(f"{meta} has different settings. Use the same options to continue, or a new --run name to start over.")
    run_dir.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(conf, ensure_ascii=False), encoding="utf-8")
    g = Game(run_dir, a.seed, players, a.rounds, a.max_days, a.reveal_models, a.dry_run, config, fixed)
    print(f"Winner: {g.play()}  -> {run_dir / 'transcript.md'}")


if __name__ == "__main__":
    main()
