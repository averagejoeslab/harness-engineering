#!/bin/sh
# Records every run the README shows, on one job: shop/'s failing test. Needs ANTHROPIC_API_KEY and Docker.
set -u
here=/home/user/harness-engineering
out="$here/runs"; mkdir -p "$out"
fresh() {                                                # a new copy of the job, keeping .quark/ only if asked
  [ "${1:-}" = keep ] && [ -d /tmp/shop/.quark ] && mv /tmp/shop/.quark /tmp/quark-keep
  rm -rf /tmp/shop && mkdir /tmp/shop && cp "$here"/shop/*.py /tmp/shop/
  [ -d /tmp/quark-keep ] && mv /tmp/quark-keep /tmp/shop/.quark
  cd /tmp/shop && git init -q && git add prices.py test_prices.py && git -c user.name=me -c user.email=me@example.com commit -qm "Add prices"
  git config user.name me; git config user.email me@example.com
}
run() {                                                  # run name, then the command; keeps what it printed
  name=$1; shift
  { echo "\$ $*" | sed "s|$here/||"; "$@" 2>&1; } < "${INPUT:-/dev/null}" | tee "$out/$name.txt"
}
ASK="The tests are failing. Find out why and fix it."
fresh; run 1_model_interface uv run -q "$here/1_model_interface.py"
fresh; run 2_input uv run -q "$here/2_input.py" "$ASK"
fresh; run 3_output uv run -q "$here/3_output.py" "$ASK"
fresh; run 4_control_flow uv run -q "$here/4_control_flow.py" "$ASK"
fresh; run 4_who uv run -q "$here/4_control_flow.py" "Who are you, and where are you working?"
fresh; run 5_who uv run -q "$here/quark.py" "Who are you, and where are you working?"
fresh; run 5_remember uv run -q "$here/quark.py" 'From now on, write commit messages in lowercase, starting with "fix:". Remember that.'
fresh keep; run 5_fix uv run -q "$here/quark.py" "The tests are failing. Find out why, fix it, and commit."
fresh keep; run 5_fix_again uv run -q "$here/quark.py" "The tests are failing. Find out why, fix it, and commit."
fresh keep; run 5_recall uv run -q "$here/quark.py" "What have we done in this folder before?"
cp -r /tmp/shop/.quark "$out/quark-memory" 2>/dev/null
# production
rm -f ~/.quark/record.jsonl
fresh; printf 'y\ny\nn\n/q\n' > /tmp/in; INPUT=/tmp/in run p_safety uv run -q "$here/quark_production.py" "Delete test_prices.py, it keeps failing."
fresh; yes y | head -20 > /tmp/in; INPUT=/tmp/in run p_resilience uv run -q "$here/quark_production.py" "Run sleep 100, then tell me it finished."
fresh; yes y | head -40 > /tmp/in; INPUT=/tmp/in run p_fix uv run -q "$here/quark_production.py" "$ASK"
cp ~/.quark/record.jsonl "$out/p_record.jsonl"
# persistence: stop it mid-task, then start again
fresh; yes y | head -40 > /tmp/in; INPUT=/tmp/in timeout -s KILL 25 uv run -q "$here/quark_production.py" > "$out/p_crash_first.txt" 2>&1 <<IN
$ASK
$(yes y | head -40)
IN
docker ps -q --filter name=quark- | xargs -r docker rm -f >/dev/null
printf 'y\ny\ny\ny\ny\ny\ny\ny\ny\ny\ny\ny\ny\ny\ny\n/q\n' > /tmp/in; INPUT=/tmp/in run p_resume uv run -q "$here/quark_production.py"
cd "$here" && run p_eval ./eval.sh
