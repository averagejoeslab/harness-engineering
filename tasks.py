# Evaluation: tasks with known right answers, each run in a fresh copy of shop/, checked by what the agent did, not what it says.
# uv run tasks.py                    evaluates harness.py
# uv run tasks.py harness_prod.py    evaluates the production harness (needs Docker)
import subprocess, sys, os, re, shutil, tempfile, platform

here = os.path.dirname(os.path.abspath(__file__))       # the repo, wherever this is run from
harness = sys.argv[1] if len(sys.argv) > 1 else "harness.py"

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def os_names():                                          # the system's name, or its distribution's
    names = [platform.system()]
    try: names += re.findall(r'^NAME="?([^"\n]+)', open("/etc/os-release").read(), re.M)
    except OSError: pass
    return names

def unchanged():
    return not [l for l in sh("git status --porcelain").stdout.splitlines() if "__pycache__" not in l and ".harness" not in l]

def count_works():
    return sh('python3 -c "from prices import count; assert count([(10, 2), (5, 1)]) == 3 and count([]) == 0"').returncode == 0

def read(name):
    return open(name).read() if os.path.exists(name) else ""

tasks = [                                                # the request, and how to tell it was done right
    ("The tests are failing. Find out why and fix it.",
     lambda said: sh("python3 -m unittest -q").returncode == 0 and sh("git diff --quiet HEAD -- test_prices.py").returncode == 0),
    ("Add a function count(items) to prices.py that returns how many items are in the basket, counting quantities.",
     lambda said: count_works()),
    ("Write the names of the .py files in this folder, one per line, sorted, into files.txt.",
     lambda said: read("files.txt") == "prices.py\ntest_prices.py\n"),
    ("What does total() return for an empty basket? Don't change anything.",
     lambda said: unchanged() and re.search(r"\b0\b", said) is not None),
    ("Which operating system is this computer running? Write just its name into os.txt.",
     lambda said: any(n.lower() in read("os.txt").lower() for n in os_names())),
]

passed = 0
for request, done_right in tasks:
    os.chdir(tempfile.mkdtemp())                         # a fresh copy of shop/, as a git repo
    for f in os.listdir(os.path.join(here, "shop")):
        if f.endswith(".py"): shutil.copy(os.path.join(here, "shop", f), f)
    sh("git init -q && git add . && git -c user.name=eval -c user.email=eval@example.com commit -qm start")
    said = subprocess.run(["uv", "run", "-q", os.path.join(here, harness), request], input="y\n" * 50,
                          capture_output=True, text=True).stdout
    ok = done_right(said)
    passed += ok
    print(("PASS  " if ok else "FAIL  ") + request, flush=True)
print(f"{passed}/{len(tasks)} passed")
