#!/bin/sh
# Records every run the README shows, on one job: shop/'s failing test. Needs a key in .env, and Docker.
set -u
here=$(cd "$(dirname "$0")" && pwd)
out="$here/runs"; rm -rf "$out"; mkdir -p "$out"
fresh() {                                                # a new copy of the job; "keep" carries quark's memory over
  [ "${1:-}" = keep ] && [ -d /tmp/shop/.quark ] && mv /tmp/shop/.quark /tmp/quark-keep
  rm -rf /tmp/shop && mkdir /tmp/shop && cp "$here"/shop/*.py /tmp/shop/
  [ -d /tmp/quark-keep ] && mv /tmp/quark-keep /tmp/shop/.quark
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
fresh; run 1_model_interface 1_model_interface.py
fresh; run 2_input 2_input.py "$ASK"
fresh; run 3_output 3_output.py "$ASK"
fresh; run 4_control_flow 4_control_flow.py "$ASK"
fresh; run 4_who 4_control_flow.py "Who are you, and where are you working?"
fresh; run 5_who quark.py "Who are you, and where are you working?"
fresh; run 5_remember quark.py 'From now on, write commit messages in lowercase, starting with "fix:". Remember that.'
fresh keep; run 5_fix quark.py "The tests are failing. Find out why, fix it, and commit."
fresh keep; run 5_fix_again quark.py "The tests are failing. Find out why, fix it, and commit."
fresh keep; run 5_recall quark.py "What have we done in this folder before?"
cp -r /tmp/shop/.quark "$out/quark-memory"
# production
rm -f "$HOME/.quark/record.jsonl"
fresh; ANSWERS='y\ny\nn\nn\nn\n' run p_safety quark_production.py "Delete test_prices.py, it keeps failing."
fresh; ANSWERS='y\ny\ny\ny\n' run p_resilience quark_production.py "Run sleep 100, then tell me it finished."
fresh; ANSWERS="$(printf 'y\\n%.0s' $(seq 30))" run p_fix quark_production.py "$ASK"
cp "$HOME/.quark/record.jsonl" "$out/p_record.jsonl"
# persistence: stopped partway through, then started again
fresh; { printf '%s\n' "$ASK"; sleep 12; printf 'y\n'; sleep 600; } | timeout -s KILL 40 uv run -q --env-file "$here/.env" "$here/quark_production.py" > "$out/p_stopped.txt" 2>&1
docker ps -aq --filter name=quark- | xargs -r docker rm -f > /dev/null
echo "--- p_stopped"; cat "$out/p_stopped.txt"; echo; tail -3 /tmp/shop/.quark/episodes/*.jsonl | cut -c1-200
ANSWERS="y\n$(printf 'y\\n%.0s' $(seq 30))/q\n" run p_resume quark_production.py
cd "$here" && echo '$ ./eval.sh' > "$out/p_eval.txt" && ./eval.sh >> "$out/p_eval.txt" 2>&1; echo "--- p_eval"; cat "$out/p_eval.txt"
