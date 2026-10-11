#!/bin/sh
# Records every run the README shows, on one job: shop/'s failing test. Needs a key in .env, and Docker.
set -u
here=$(cd "$(dirname "$0")" && pwd)
out="$here/runs"; rm -rf "$out"; mkdir -p "$out"
fresh() {                                                # a new copy of the job, as a git repo
  rm -rf /tmp/shop && mkdir /tmp/shop && cp "$here"/shop/*.py /tmp/shop/
  cd /tmp/shop && git init -q && git add prices.py test_prices.py && git -c user.name=me -c user.email=me@example.com commit -qm "Add prices"
  git config user.name me && git config user.email me@example.com
}
run() {                                                  # run <name> <file> [request]: keeps what it printed; answers come from $ANSWERS
  name=$1; file=$2; shift 2
  echo "\$ uv run $file${1:+ \"$1\"}" > "$out/$name.txt"
  printf "${ANSWERS:-}" | timeout 600 uv run -q --env-file "$here/.env" "$here/$file" "$@" >> "$out/$name.txt" 2>&1
  echo "--- $name"; cat "$out/$name.txt"
}
ASK="The tests are failing. Find out why and fix it."
# building it, one part at a time
fresh; run 1_model_interface 1_model_interface.py
fresh; run 2_input 2_input.py "$ASK"
fresh; run 3_output 3_output.py "$ASK"
fresh; run 4_control_flow 4_control_flow.py "$ASK"
fresh; run 4_who 4_control_flow.py "Who are you, and where are you working?"
fresh; run 5_who harness.py "Who are you, and where are you working?"
# production
rm -f "$HOME/.harness/record.jsonl"
# persistence: memory, in one folder that keeps its history
Y="$(printf 'y\\n%.0s' $(seq 30))"
fresh
ANSWERS="$Y" run p_remember harness_production.py 'From now on, write commit messages in lowercase, starting with "fix:". Remember that.'
ANSWERS="$Y" run p_fix_commit harness_production.py "The tests are failing. Find out why, fix it, and commit."
ANSWERS="$Y" run p_recall harness_production.py "What have we done in this folder before?"
fresh; ANSWERS="$(printf 'y\\n%.0s' $(seq 30))" run p_fix harness_production.py "$ASK"
cp "$HOME/.harness/record.jsonl" "$out/p_record.jsonl"
fresh; ANSWERS='y\nn\n' run p_safety harness_production.py "Delete test_prices.py, it keeps failing."
fresh; ANSWERS='y\ny\ny\n' run p_resilience harness_production.py "Run sleep 100 as a single command, then tell me it finished."
fresh; { printf '%s\n' "$ASK"; sleep 12; printf 'y\n'; sleep 600; } | timeout -s KILL 40 uv run -q --env-file "$here/.env" "$here/harness_production.py" > "$out/p_stopped.txt" 2>&1
docker ps -aq --filter name=harness- | xargs -r docker rm -f > /dev/null
echo "--- p_stopped"; cat "$out/p_stopped.txt"
ANSWERS='y\ny\ny\ny\n/q\n' run p_resume harness_production.py
cd "$here" && echo '$ ./eval.sh' > "$out/p_eval.txt" && ./eval.sh >> "$out/p_eval.txt" 2>&1; echo "--- p_eval"; cat "$out/p_eval.txt"
