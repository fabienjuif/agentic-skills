#!/usr/bin/env python3
"""ETA stats collector (hook mode) and renderer (render/keys modes).

Stdlib only so it runs the same on macOS, Linux and Windows. The model never does the
arithmetic or the clock: it passes steps in, this prints the final block verbatim.
"""
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(os.environ.get("ETA_HOME") or Path.home() / ".claude" / "eta")
LOG = DATA / "log.jsonl"
PENDING = DATA / "pending"
ERRORS = DATA / "hook-errors.log"

MIN_LOGGED_S = 2  # faster commands never need an ETA and would drown the log
MIN_SAMPLES = 3  # below this a median is noise: report unknown instead of a number
WINDOW = 50  # recent samples only, toolchains and machines drift
BAR = 10

# Navigation and output filters around the real command ("make ci-fast > log; tail log")
TRIVIAL = {"cd", "export", "source", "set", "echo", "true", ":", "unset", "pushd", "popd",
           "tail", "head", "cat", "grep", "rg", "wc", "ls", "date", "pwd", "sleep",
           "df", "du", "free", "uptime", "printf", "which", "stat", "nproc",
           "sed", "awk", "cut", "sort", "uniq", "tr"}
WRAPPERS = {"sudo", "time", "env", "nice", "command", "exec", "nohup", "timeout"}
# Local git bookkeeping is never the slow part; keeping it in a key only dilutes the real command
GIT_QUICK = {"status", "diff", "log", "show", "rev-parse", "rev-list", "branch", "worktree", "add",
             "commit", "stash", "checkout", "switch", "restore", "reset", "rm", "mv", "tag", "config"}
SHELL_KW = {"for", "while", "if", "case", "do", "done", "then", "fi", "function"}


# ---------- collection ----------


def repo_of(cwd):
    # absolute root path, not the dir name: same-named repos must not share timings
    p = Path(cwd).resolve()
    for d in (p, *p.parents):
        g = d / ".git"
        if g.is_dir():
            return str(d)
        if g.is_file():
            # worktree: key on the main checkout so every worktree shares the same stats
            m = re.match(r"gitdir:\s*(.+?)[\\/]\.git[\\/]worktrees[\\/]", g.read_text().strip())
            return str(Path(m.group(1)).resolve()) if m else str(d)
    return str(p)


def seg_key(toks):
    toks = list(toks)
    while toks and (toks[0] in WRAPPERS or re.match(r"^\w+=", toks[0])):
        w = toks.pop(0)
        if w == "timeout" and toks and re.fullmatch(r"\d+(\.\d+)?[smhd]?", toks[0]):
            toks.pop(0)
        elif w == "nice":
            if toks[:1] == ["-n"]:
                del toks[:2]
            elif toks and re.fullmatch(r"-\d+", toks[0]):
                toks.pop(0)
    if not toks or toks[0] in TRIVIAL:
        return None
    if toks[0] in SHELL_KW:
        raise ValueError("shell script")
    prog = re.sub(r"\.(exe|cmd|bat)$", "", Path(toks[0]).name)
    if not re.fullmatch(r"[A-Za-z][\w.+-]*", prog):
        raise ValueError("not a program")
    if prog in ("bash", "sh", "zsh", "python", "python3", "node"):
        # "bash tools/x.sh" and "./tools/x.sh" are the same job: key on the script
        if toks[1:2] in (["-c"], ["-e"]):
            raise ValueError("inline code")  # one-off, never repeats
        script = next((t for t in toks[1:] if not t.startswith("-")), "")
        if re.search(r"\.(sh|py|js|mjs)$", script):
            return Path(script).name
    words = []
    for t in toks[1:]:
        if not re.match(r"^[A-Za-z][\w:-]*$", t):
            break
        words.append(t)
    if prog == "git" and words[:1] and words[0] in GIT_QUICK:
        return None
    # "npm run build" and "docker compose up" carry the real target one word further
    keep = 2 if words and words[0] in ("run", "compose") else 1
    return " ".join([prog, *words[:keep]])


def segments(cmd):
    """Simple commands of a shell line: split on && || ; and keep only the head of a pipeline.

    shlex (stdlib, same on every OS) tokenises quotes and operators properly, so a quoted
    "&&" is not a separator. Not a full bash grammar: subshells, heredocs and loops raise.
    """
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    segs, cur, skip = [], [], False
    toks = iter(lex)
    for t in toks:
        if t in ("&&", "||", ";", "&"):
            segs.append(cur)
            cur, skip = [], False
        elif t == "|":
            skip = True  # what follows is a filter on the real command's output
        elif t == "(" and (skip or (cur and cur[-1].endswith("$"))):
            depth = 1  # $( ... ) command substitution: the body is not the command
            for u in toks:
                depth += (u == "(") - (u == ")")
                if depth == 0:
                    break
            if not skip:
                cur[-1] += "()"
        elif t in ("(", ")") or t.startswith("<<"):
            raise ValueError("not a simple command")
        elif re.fullmatch(r"[<>]+&?", t):
            next(toks, None)  # redirection target
        elif not skip:
            cur.append(t)
    segs.append(cur)
    return segs


def normalize(cmd):
    # Heredocs, loops and long chains are one-offs that never repeat: logging them
    # only produced junk keys.
    flat = cmd.replace("\\\n", " ")
    if "\n" in flat.strip():
        return None
    try:
        keys = [k for k in (seg_key(x) for x in segments(flat)) if k]
    except ValueError:  # includes shlex's unbalanced-quote error
        return None
    return " && ".join(keys) if 0 < len(keys) <= 3 else None


def append(rec):
    DATA.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")


def hook():
    ev = json.load(sys.stdin)
    name = ev.get("hook_event_name")
    now = time.time()
    sid = ev.get("session_id", "x")
    repo = repo_of(ev.get("cwd") or os.getcwd())
    PENDING.mkdir(parents=True, exist_ok=True)

    if name in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        if ev.get("tool_name") != "Bash":
            return
        tin = ev.get("tool_input") or {}
        if tin.get("run_in_background"):
            return  # returns instantly, the duration would be meaningless
        if "eta.py" in tin.get("command", ""):
            return  # `eta.py run` logs itself, and eta's own calls are not work to time
        slot = PENDING / re.sub(r"\W", "_", ev.get("tool_use_id", ""))
        if name == "PreToolUse":
            for old in PENDING.iterdir():
                if now - old.stat().st_mtime > 86400:
                    old.unlink(missing_ok=True)
            slot.write_text(str(now))
            return
        started = float(slot.read_text()) if slot.exists() else None
        slot.unlink(missing_ok=True)
        # duration_ms (if the harness sends it) excludes permission prompts, the pair does not
        if ev.get("duration_ms") is not None:
            dur = ev["duration_ms"] / 1000
        elif started is not None:
            dur = now - started
        else:
            return
        key = normalize(tin.get("command", ""))
        if key and dur >= MIN_LOGGED_S:
            append({"t": int(now), "repo": repo, "key": key, "s": round(dur, 1),
                    "ok": name == "PostToolUse"})
    elif name == "UserPromptSubmit":
        (PENDING / f"turn-{sid}").write_text(str(now))
    elif name == "Stop":
        slot = PENDING / f"turn-{sid}"
        if slot.exists():
            dur = now - float(slot.read_text())
            slot.unlink(missing_ok=True)
            if dur >= MIN_LOGGED_S:
                append({"t": int(now), "repo": repo, "key": "turn", "s": round(dur, 1), "ok": True})


# ---------- stats ----------


def load(repo):
    out = {}
    if LOG.exists():
        with LOG.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("repo") == repo and r.get("ok"):
                    out.setdefault(r["key"], []).append(r["s"])
    return {k: v[-WINDOW:] for k, v in out.items()}


def spread(samples):
    s = sorted(samples)
    q = statistics.quantiles(s, n=4, method="inclusive")
    p90 = statistics.quantiles(s, n=10, method="inclusive")[8]
    return q[0], q[1], p90


# ---------- formatting ----------


def fmt(s):
    s = round(s)
    if s < 90:
        return f"{s} s"
    m = round(s / 60)
    return f"{m} min" if m < 90 else f"{m // 60} h {m % 60:02d}"


def fmt_range(lo, hi):
    if hi >= 90:  # keep one unit on both sides: "1-2 min", not "60 s-2 min"
        a, b = round(lo / 60), round(hi / 60)
        return f"{a}-{b} min" if a != b else f"{b} min"
    return f"{round(lo)}-{round(hi)} s"


def clock(base, s):
    t = base + timedelta(seconds=s)
    return t.strftime("%H:%M") + (" (+1d)" if t.date() != base.date() else "")


UNITS = {"s": 1, "m": 60, "h": 3600}


def parse_dur(spec):
    """'90', '90s', '2m', '1-2m', '30s-2m' -> (low, mid, high) seconds, or None."""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([smh])?(?:-(\d+(?:\.\d+)?)([smh])?)?", spec.strip())
    if not m:
        return None
    a, ua, b, ub = m.groups()
    ua = ua or ub or "s"
    lo = float(a) * UNITS[ua]
    if b is None:
        return lo * 0.7, lo, lo * 1.5  # a lone guess gets a wide band
    hi = float(b) * UNITS[ub or ua]
    return lo, (lo + hi) / 2, hi


class Step:
    def __init__(self, raw, stats):
        parts = (raw.split("|", 4) + ["", "", "", ""])[:5]
        self.status, self.name, est, el, self.lane = (p.strip() for p in parts)
        if self.status not in ("done", "running", "todo"):
            sys.exit(f"eta: bad status {self.status!r} in --step {raw!r}")
        self.elapsed = float(el) if el else 0.0
        # "est>actual" on a done step; a lone value on a done step is what it took
        est, sep, act = est.partition(">")
        if self.status == "done" and not sep:
            est, act = "", est
        self.band = None  # (low, mid, high) seconds
        self.source = None  # "stats" | "guess"
        self.n = 0
        self.shown = "-"
        self.why = None  # reason the estimate is unknown
        if est.startswith("@"):
            key = est[1:]
            samples = stats.get(key, [])
            if len(samples) >= MIN_SAMPLES:
                self.band, self.source, self.n = spread(samples), "stats", len(samples)
                self.shown = f"~{fmt(self.band[1])}"
            else:
                self.shown = "?"
                self.why = f"{self.name}: {len(samples)} sample(s) for '{key}'"
        elif est in ("", "?"):
            self.shown = "-" if self.status == "done" else "?"
            if self.status != "done":
                self.why = f"{self.name}: no estimate"
        else:
            self.band = parse_dur(est)
            if self.band is None:
                sys.exit(f"eta: bad estimate {est!r} in --step {raw!r}")
            self.source = "guess"
            lo, mid, hi = self.band
            explicit_range = "-" in est
            self.shown = fmt_range(lo, hi) if explicit_range else (
                fmt(mid) if self.status == "done" else f"~{fmt(mid)}")
        self.est_mid = self.band[1] if self.band else None  # kept for the "diff" column
        self.actual = None
        if self.status == "done":
            done_band = parse_dur(act) if act.strip() else None
            if act.strip() and done_band is None:
                sys.exit(f"eta: bad duration {act!r} in --step {raw!r}")
            # a done step counts by what it took, not by what was expected
            self.actual = done_band[1] if done_band else None
            self.band = done_band
        elif self.status == "running" and self.elapsed:
            self.actual = self.elapsed


def delta(s):
    """Actual vs estimate, absolute and relative; a running step only once it overruns."""
    if s.est_mid is None or not s.actual or (s.status == "running" and s.actual <= s.est_mid):
        return "-"
    d = s.actual - s.est_mid
    return f"{'+' if d >= 0 else '-'}{fmt(abs(d))} ({d / s.est_mid * 100:+.0f}%)"


def render(args):
    cwd, waiting, raws = os.getcwd(), None, []
    it = iter(args)
    for a in it:
        if a == "--cwd":
            cwd = next(it)
        elif a == "--waiting":
            waiting = next(it)
        elif a == "--step":
            raws.append(next(it))
        else:
            sys.exit(f"eta: unknown argument {a!r}")
    if not raws:
        sys.exit("eta: need at least one --step")
    stats = load(repo_of(cwd))
    steps = [Step(r, stats) for r in raws]
    base = datetime.now()

    todo = [s for s in steps if s.status != "done"]
    unknown = [s.why for s in todo if s.band is None]
    if waiting:
        unknown.append(f"waiting on you: {waiting}")

    # ETA
    eta_text, overrun = None, False
    if not unknown and todo:
        lanes = {}
        work = weight_stats = 0.0
        for s in todo:
            band = s.band
            if s.status == "running" and s.elapsed:
                shifted = tuple(max(x - s.elapsed, 0) for x in band)
                if shifted[2] == 0:  # past even the high end, the number is no longer trustworthy
                    overrun = True
                    shifted = (0, band[1] * 0.2, band[1] * 0.5)
                elif shifted[1] == 0:  # past the midpoint only: the ETA must keep shrinking, not jump
                    shifted = (0, shifted[2] / 2, shifted[2])
                band = shifted
            # two steps running at once are parallel by definition, whether or not the
            # caller named lanes
            lane = s.lane or (f"running:{id(s)}" if s.status == "running" else "")
            acc = lanes.setdefault(lane, [0.0, 0.0, 0.0])
            for i in range(3):
                acc[i] += band[i]
            work += band[1]
            if s.source == "stats":
                weight_stats += band[1]
        # named lanes run in parallel (the slowest decides); steps without a lane run in
        # sequence around them, e.g. the integration after two parallel branches
        seq = lanes.pop("", [0.0, 0.0, 0.0])
        lo, mid, hi = (seq[i] + max((a[i] for a in lanes.values()), default=0.0) for i in range(3))
        share = weight_stats / work if work else 0
        min_n = min((s.n for s in todo if s.source == "stats"), default=0)
        if overrun or share < 0.5:
            conf = "low"
        elif share == 1 and min_n >= 5:
            conf = "high"
        else:
            conf = "medium"
        c_lo, c_hi = clock(base, lo), clock(base, hi)
        window = f", between {c_lo} and {c_hi}" if c_lo != c_hi else ""
        eta_text = f"ETA {clock(base, mid)} (~{fmt(mid)}{window}) · confidence: {conf}"
    elif not todo:
        eta_text = "done"
    else:
        eta_text = "ETA unknown (" + "; ".join(unknown) + ")"

    # progress: by time when every step has a duration, else by step count
    done = [s for s in steps if s.status == "done"]
    if all(s.band for s in steps) and not unknown:
        spent = sum(s.band[1] for s in done) + sum(s.elapsed for s in steps if s.status == "running")
        left = sum(max(s.band[1] - s.elapsed, 0) for s in todo)
        pct = spent / (spent + left) if spent + left else 1.0
    else:
        pct = len(done) / len(steps)
    pct = min(max(pct, 0.0), 0.99 if todo else 1.0)  # never claim 100% while a step is open
    filled = round(pct * BAR)

    label = {"done": "✔ done", "running": "▶ running", "todo": "· todo"}
    rows = ["| step | status | est | actual | diff |", "|---|---|---|---|---|"]
    rows += [f"| {s.name} | {label[s.status]} | {s.shown} | {fmt(s.actual) if s.actual else '-'} | {delta(s)} |"
             for s in steps]
    print(f"[{'█' * filled}{'░' * (BAR - filled)}] {round(pct * 100)}% · {eta_text}")
    print()
    print("\n".join(rows))
    print()
    print(f"waiting on you: {waiting or 'nothing'}")


def keys(args):
    cwd = args[1] if args[:1] == ["--cwd"] and len(args) > 1 else os.getcwd()
    rows = []
    for k, v in load(repo_of(cwd)).items():
        if len(v) >= MIN_SAMPLES:
            lo, mid, hi = spread(v)
            rows.append((mid, f"{k}\tn={len(v)}\tp50={fmt(mid)}\tp90={fmt(hi)}"))
    for _, line in sorted(rows, reverse=True):
        print(line)
    if not rows:
        print("(no key with enough samples yet)")


def run(args):
    """Time a command the hooks cannot see (run_in_background) and log it like they would."""
    cmd = args[1:] if args[:1] == ["--"] else args
    if not cmd:
        sys.exit("usage: eta.py run -- <command> [args...]")
    start = time.time()
    rc = subprocess.call(cmd)
    dur = time.time() - start
    key = normalize(" ".join(cmd))
    if key and dur >= MIN_LOGGED_S:
        append({"t": int(time.time()), "repo": repo_of(os.getcwd()), "key": key,
                "s": round(dur, 1), "ok": rc == 0})
    sys.exit(rc)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    mode, rest = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if mode == "hook":
        # a broken stats hook must never block or fail a session
        try:
            hook()
        except Exception as e:  # noqa: BLE001
            try:
                DATA.mkdir(parents=True, exist_ok=True)
                with ERRORS.open("a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} {e!r}\n")
            except OSError:
                pass
    elif mode == "render":
        render(rest)
    elif mode == "keys":
        keys(rest)
    elif mode == "run":
        run(rest)
    else:
        sys.exit("usage: eta.py hook | run -- CMD | render [--cwd D] [--waiting T] --step 'status|name|est|elapsed|lane' ... | keys [--cwd D]")


if __name__ == "__main__":
    main()
