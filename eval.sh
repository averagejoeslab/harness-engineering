#!/bin/sh
# Evaluation: tasks with known right answers, each run in a fresh copy of shop/, checked by what the agent did, not what it says.
# ./eval.sh                          evaluates harness.py
# ./eval.sh harness_production.py    evaluates the production harness (needs Docker)
harness=${1:-harness.py}
here=$(cd "$(dirname "$0")" && pwd)                     # the repo, wherever this is run from
env=$([ -f "$here/.env" ] && echo --env-file "$here/.env")
passed=0; total=0
check() {                                                # $1: the request; $2: true only if it was done right
  cd "$(mktemp -d)" && cp "$here"/shop/*.py . && git init -q && git add . && git -c user.name=eval -c user.email=eval@example.com commit -qm start
  said=$(yes | uv run -q $env "$here/$harness" "$1" 2>/dev/null); export said
  total=$((total + 1))
  if sh -c "$2" > /dev/null 2>&1; then passed=$((passed + 1)); echo "PASS  $1"; else echo "FAIL  $1"; fi
  cd "$here"
}
unchanged='test -z "$(git status --porcelain | grep -v -e __pycache__ -e .harness)"'
check "The tests are failing. Find out why and fix it." \
      'python3 -m unittest -q && git diff --quiet HEAD -- test_prices.py'
check "Add a function count(items) to prices.py that returns how many items are in the basket, counting quantities." \
      'python3 -c "from prices import count; assert count([(10, 2), (5, 1)]) == 3 and count([]) == 0"'
check "Write the names of the .py files in this folder, one per line, sorted, into files.txt." \
      'printf "prices.py\ntest_prices.py\n" | cmp -s - files.txt'
check "What does total() return for an empty basket? Don't change anything." \
      "$unchanged"' && echo "$said" | grep -qw 0'
check "Which operating system is this computer running? Write just its name into os.txt." \
      'grep -qi -e "$(uname -s)" -e "$(. /etc/os-release 2>/dev/null; echo "${NAME:-$(uname -s)}")" os.txt'   # the system's name, or its distribution's
echo "$passed/$total passed"
