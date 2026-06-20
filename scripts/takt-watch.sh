#!/usr/bin/env bash
#
# takt-watch.sh - TAKT 実行セッションをリアルタイム監視する
#
# TAKT が `.takt/runs/<timestamp>-<slug>/` 配下に出力する成果物を `tail -f` で
# 追尾し、JSONL ログのイベントを人間が読みやすい形に整形して表示する。
#
# Usage:
#   scripts/takt-watch.sh                  # 最新の run を監視
#   scripts/takt-watch.sh <slug|run-dir>   # 指定 run を監視 (部分一致可)
#   scripts/takt-watch.sh -l               # run 一覧を表示して終了
#   scripts/takt-watch.sh -r               # 直近の AI 出力 (response) を表示して終了
#   scripts/takt-watch.sh -h               # ヘルプ
#
# Options:
#   -l, --list      run 一覧を表示
#   -r, --response  最新 run の直近 AI 出力を表示 (context/previous_responses)
#   -n, --no-follow tail -f せず、既存ログを 1 回だけ整形表示
#   -h, --help      ヘルプ
#
set -euo pipefail

# --- 設定 -------------------------------------------------------------------
RUNS_DIR="${TAKT_RUNS_DIR:-.takt/runs}"

# --- 色 (TTY のときだけ) ----------------------------------------------------
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_DIM=$'\033[2m'; C_BOLD=$'\033[1m'
  C_BLUE=$'\033[34m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'; C_CYAN=$'\033[36m'; C_MAGENTA=$'\033[35m'
else
  C_RESET=; C_DIM=; C_BOLD=; C_BLUE=; C_GREEN=; C_YELLOW=; C_RED=; C_CYAN=; C_MAGENTA=
fi

err() { printf '%s\n' "$*" >&2; }

usage() {
  sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# --- run ディレクトリ解決 ---------------------------------------------------
list_runs() {
  if [[ ! -d "$RUNS_DIR" ]]; then
    err "run ディレクトリが見つかりません: $RUNS_DIR"
    exit 1
  fi
  local d meta status step iter wf
  printf '%s%-38s %-9s %-16s %s%s\n' "$C_BOLD" "RUN" "STATUS" "STEP" "WORKFLOW" "$C_RESET"
  while IFS= read -r d; do
    meta="$d/meta.json"
    status="-"; step="-"; iter="-"; wf="-"
    if [[ -f "$meta" ]]; then
      status=$(python3 -c "import json,sys;d=json.load(open('$meta'));print(d.get('status','-'))" 2>/dev/null || echo "-")
      step=$(python3 -c "import json,sys;d=json.load(open('$meta'));print(d.get('currentStep','-'))" 2>/dev/null || echo "-")
      iter=$(python3 -c "import json,sys;d=json.load(open('$meta'));print(d.get('currentIteration','-'))" 2>/dev/null || echo "-")
      wf=$(python3 -c "import json,sys;d=json.load(open('$meta'));print(d.get('workflow','-'))" 2>/dev/null || echo "-")
    fi
    printf '%-38s %-9s %-16s %s\n' "$(basename "$d")" "$status" "$step (i$iter)" "$wf"
  done < <(ls -dt "$RUNS_DIR"/*/ 2>/dev/null)
}

resolve_run() {
  local arg="${1:-}"
  if [[ -z "$arg" ]]; then
    ls -dt "$RUNS_DIR"/*/ 2>/dev/null | head -1 | sed 's:/*$::'
    return
  fi
  # 絶対/相対パスでディレクトリ指定された場合
  if [[ -d "$arg" ]]; then
    printf '%s\n' "${arg%/}"
    return
  fi
  # slug 部分一致 (最新優先)
  ls -dt "$RUNS_DIR"/*"$arg"*/ 2>/dev/null | head -1 | sed 's:/*$::'
}

print_header() {
  local run="$1"
  local meta="$run/meta.json"
  printf '%s%s═══ TAKT watch ═══════════════════════════════════════════%s\n' "$C_BOLD" "$C_CYAN" "$C_RESET"
  printf '%srun     %s%s\n' "$C_DIM" "$C_RESET" "$(basename "$run")"
  if [[ -f "$meta" ]]; then
    python3 - "$meta" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
def row(k, v): print(f"\033[2m{k:<8}\033[0m{v}")
row("task", d.get("task", "-"))
row("workflow", d.get("workflow", "-"))
row("status", d.get("status", "-"))
row("step", f"{d.get('currentStep','-')} (phase {d.get('phase','-')}, iter {d.get('currentIteration','-')})")
row("updated", d.get("updatedAt", "-"))
PY
  fi
  printf '%s──────────────────────────────────────────────────────────%s\n' "$C_DIM" "$C_RESET"
}

# JSONL 1 行を整形 (stdin -> stdout)。色は環境変数で受け渡す。
format_stream() {
  C_RESET="$C_RESET" C_DIM="$C_DIM" C_BOLD="$C_BOLD" C_BLUE="$C_BLUE" \
  C_GREEN="$C_GREEN" C_YELLOW="$C_YELLOW" C_RED="$C_RED" C_CYAN="$C_CYAN" \
  C_MAGENTA="$C_MAGENTA" python3 -u -c '
import sys, os, json

R=os.environ; RESET=R["C_RESET"]; DIM=R["C_DIM"]; BOLD=R["C_BOLD"]
BLUE=R["C_BLUE"]; GREEN=R["C_GREEN"]; YELLOW=R["C_YELLOW"]
RED=R["C_RED"]; CYAN=R["C_CYAN"]; MAGENTA=R["C_MAGENTA"]

def ts(o):
    t = o.get("timestamp") or o.get("startTime") or o.get("endTime") or ""
    return t[11:19] if len(t) >= 19 else ""

def short(s, n=400):
    s = (s or "").strip().replace(chr(10), " ")
    return s if len(s) <= n else s[:n] + " …"

def emit(s):
    print(s); sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    t = o.get("type", "?")
    tm = (DIM + ts(o) + RESET + " ") if ts(o) else ""
    if t == "workflow_start":
        emit(tm + BOLD + CYAN + "▶ workflow start" + RESET + " " + str(o.get("workflowName","")) + "  task: " + short(o.get("task"),120))
    elif t == "workflow_complete":
        emit(tm + BOLD + GREEN + "■ workflow complete" + RESET + " (" + str(o.get("iterations","?")) + " iterations)")
    elif t == "interactive_start":
        emit(tm + DIM + "… interactive (待機)" + RESET)
    elif t == "interactive_end":
        emit(tm + DIM + "… interactive end (confirmed=" + str(o.get("confirmed")) + ")" + RESET)
    elif t == "step_start":
        emit(tm + BOLD + BLUE + "● step start" + RESET + " " + BOLD + str(o.get("step")) + RESET + "  persona=" + str(o.get("persona","-")) + "  iter=" + str(o.get("iteration","-")))
    elif t == "step_complete":
        st = o.get("status","")
        col = GREEN if st == "done" else YELLOW
        emit(tm + col + "○ step complete" + RESET + " " + str(o.get("step")) + "  status=" + str(st))
        c = short(o.get("content"))
        if c:
            emit("    " + DIM + c + RESET)
    elif t == "phase_start":
        emit(tm + "  " + MAGENTA + "→ phase " + str(o.get("phase")) + " start" + RESET + " " + DIM + "(" + str(o.get("phaseName","")) + ") " + str(o.get("step")) + RESET)
    elif t == "phase_complete":
        st = o.get("status","")
        col = GREEN if st == "done" else YELLOW
        emit(tm + "  " + col + "← phase " + str(o.get("phase")) + " complete" + RESET + " " + DIM + "(" + str(o.get("phaseName","")) + ") status=" + str(st) + RESET)
        c = short(o.get("content"))
        if c:
            emit("    " + DIM + c + RESET)
    elif t == "phase_judge_stage":
        emit(tm + "  " + YELLOW + "⚖ judge" + RESET + " stage=" + str(o.get("stage")) + " method=" + str(o.get("method")) + " status=" + str(o.get("status")))
    elif t in ("error", "workflow_error", "step_error"):
        emit(tm + BOLD + RED + "✖ " + t + RESET + " " + short(o.get("message") or o.get("error")))
    else:
        emit(tm + DIM + t + RESET + " " + short(json.dumps(o, ensure_ascii=False), 160))
'
}

show_response() {
  local run="$1"
  local resp_dir="$run/context/previous_responses"
  local f
  f=$(ls -t "$resp_dir"/*.md 2>/dev/null | head -1 || true)
  if [[ -z "$f" ]]; then
    err "AI 出力がまだありません: $resp_dir"
    exit 1
  fi
  printf '%s%s── 直近の AI 出力: %s ──%s\n' "$C_BOLD" "$C_CYAN" "$(basename "$f")" "$C_RESET"
  cat "$f"
}

# --- 引数パース -------------------------------------------------------------
FOLLOW=1
ACTION="watch"
TARGET=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    -l|--list) ACTION="list"; shift ;;
    -r|--response) ACTION="response"; shift ;;
    -n|--no-follow) FOLLOW=0; shift ;;
    -*) err "不明なオプション: $1"; usage 1 ;;
    *) TARGET="$1"; shift ;;
  esac
done

# --- 実行 -------------------------------------------------------------------
if [[ "$ACTION" == "list" ]]; then
  list_runs
  exit 0
fi

RUN=$(resolve_run "$TARGET")
if [[ -z "$RUN" || ! -d "$RUN" ]]; then
  err "対象の run が見つかりません${TARGET:+: $TARGET}"
  err "利用可能な run 一覧:"
  list_runs >&2
  exit 1
fi

if [[ "$ACTION" == "response" ]]; then
  show_response "$RUN"
  exit 0
fi

LOG=$(ls -t "$RUN"/logs/*.jsonl 2>/dev/null | head -1 || true)
if [[ -z "$LOG" ]]; then
  err "ログファイルが見つかりません: $RUN/logs/*.jsonl"
  exit 1
fi

print_header "$RUN"

if [[ "$FOLLOW" -eq 1 ]]; then
  printf '%s(Ctrl-C で終了)%s\n' "$C_DIM" "$C_RESET"
  # 既存内容も含めて追尾。tail がベース。
  tail -n +1 -f "$LOG" | format_stream
else
  format_stream < "$LOG"
fi
