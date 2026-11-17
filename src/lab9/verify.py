"""Reproduce submission evidence; every report is generated, never hand-edited.

Run from src: python -m lab9.verify
The legacy Lab 8 host-suite issue is documented separately in docs/lab9_status.md.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if not Path("lab8").is_dir():
        raise SystemExit("Run this command from src/")
    env = {**os.environ, "PYTHONUTF8": "1"}
    results = []

    def run(args: list[str], expected: int = 0) -> None:
        process = subprocess.run([sys.executable, "-m", *args], capture_output=True,
                                 text=True, encoding="utf-8", env=env)
        output = process.stdout + process.stderr
        passed = process.returncode == expected
        print(f"{'PASS' if passed else 'FAIL'} exit {process.returncode} (expected {expected}): "
              f"python -m {' '.join(args)}", flush=True)
        if not passed:
            print(output[-4000:], flush=True)
        results.append({"command": ["python", "-m", *args], "exit_code": process.returncode,
                        "expected_exit_code": expected, "passed": passed, "output": output})

    run(["lab9.smoke"])
    run(["lab9.evalset", "--build", "--check"])
    run(["lab9.evalset", "--v2", "--build"])
    run(["pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9 or advanced",
         "--basetemp=.pytest-tmp-lab9", "--tb=short"])
    for criterion, expected in (("tone", 0), ("helpful", 1)):
        run(["lab9.judge", "--csv", f"data/eval/judge_{criterion}_public.csv", "--audit", "5"], expected)
    for shape, path in (("swarm", "baseline_v1"), ("fixed", "eval_fixed"),
                        ("seeded_regression", "eval_seeded_regression"), ("swarm", "eval_pr")):
        run(["lab9.eval", "--shape", shape, "--out", f"reports/{path}.json"])
    for shape, expected in (("fixed", 0), ("seeded_regression", 1), ("pr", 0)):
        run(["lab9.gate", "--pr", f"reports/eval_{shape}.json",
             "--baseline", "reports/baseline_v1.json"], expected)
    run(["lab9.ci_check", "--pr", "reports/eval_pr.json", "--baseline", "reports/baseline_v1.json"])
    run(["lab9.mutation", "--detect"])
    spec = ["--spec", "config/metric_spec_v2.yaml"]
    baseline = ["--baseline", "reports/baseline_v2.json"]
    run(["lab9.eval", "--shape", "swarm", *spec, "--out", "reports/baseline_v2.json"])
    run(["lab9.gate", "--pr", "reports/baseline_v2.json", *baseline, *spec])
    run(["lab9.mutation", *spec, *baseline])
    run(["lab9.mutation", *spec, "--aa", "66,77,88,99,110"])
    run(["lab9.eval", "--shape", "slice_regression", *spec, "--out", "reports/eval_slice_regression.json"])
    run(["lab9.traps", "--pr", "reports/eval_slice_regression.json", *baseline, *spec])
    for trap in ("evaluator_errors_as_nan", "dropped_failing_rows", "cherry_picked_seeds", "loosened_spec"):
        args = ["lab9.gate", "--pr", f"reports/traps/{trap}.json", *baseline]
        args += (["--spec", f"reports/traps/{trap}.spec.yaml", "--base-spec", "config/metric_spec_v2.yaml"]
                 if trap == "loosened_spec" else spec)
        run(args, 1)
    sources = [*Path("lab9").glob("*.py"), *Path("config").glob("*spec*.yaml"), Path("config/fm_map.yaml")]
    sha = hashlib.sha256()
    for path in sorted(sources):
        sha.update(path.as_posix().encode())
        sha.update(path.read_bytes())
    report = {"source_sha256": sha.hexdigest(), "python": sys.version,
              "passed": all(r["passed"] for r in results), "checks": results}
    Path("reports/lab9_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{sum(r['passed'] for r in results)}/{len(results)} checks passed; reports/lab9_verification.json", flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
