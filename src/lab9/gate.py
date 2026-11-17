"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item, aggregate
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS]
    key_sets, tags = [], []
    for name, report in (("PR", pr), ("baseline", base)):
        rows, manifest = report.get("rows", []), report.get("manifest", {})
        seeds = manifest.get("seeds", [])
        if not seeds or len(seeds) != len(set(seeds)):
            problems.append(f"{name}: missing or duplicate seeds")
        keys = [(r.get("item_id"), r.get("seed")) for r in rows]
        counts = Counter(keys)
        items = {k[0] for k in keys}
        expected = {(i, seed) for i in items for seed in seeds}
        if (len(rows) != manifest.get("items", 0) * len(seeds)
                or len(items) != manifest.get("items") or set(keys) != expected
                or any(v != 1 for v in counts.values())):
            problems.append(f"{name}: incomplete or duplicate item x seed grid")
        key_sets.append(set(keys))
        item_tags = {}
        for row in rows:
            item, slices = row.get("item_id"), frozenset(row.get("slices") or [])
            if item in item_tags and item_tags[item] != slices:
                problems.append(f"{name}: inconsistent slices for {item}")
            item_tags[item] = slices
            for mid in graded:
                v = row.get(mid)
                if not isinstance(v, (int, float)) or not math.isfinite(v) or v not in (0, 1):
                    problems.append(f"{name}: invalid {mid} in {item}@{row.get('seed')}")
            if "cost" in row and (not isinstance(row["cost"], (int, float))
                                  or not math.isfinite(row["cost"]) or row["cost"] < 0):
                problems.append(f"{name}: invalid cost")
        tags.append(item_tags)
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator failures")
        for mid, value in report.get("metrics", {}).items():
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                problems.append(f"{name}: nonfinite/missing metric {mid}")
        for metric in spec["metrics"]:
            if metric["id"] not in report.get("metrics", {}):
                problems.append(f"{name}: missing aggregate {metric['id']}")
        # Verify aggregates against evidence instead of trusting a polished summary.
        if rows and all(all(isinstance(r.get(m), (bool, int, float)) for m in graded) for r in rows):
            prepared = [{**r, "cost": r.get("cost", 0)} for r in rows]
            recomputed = aggregate(prepared, graded, k_values=spec.get("pass_k", []))
            for mid, value in recomputed.items():
                actual = report.get("metrics", {}).get(mid)
                if actual is not None and value is not None and abs(actual - value) > 0.0001:
                    problems.append(f"{name}: aggregate {mid} disagrees with rows")
    if key_sets[0] != key_sets[1]:
        problems.append("PR item/seed set differs from baseline")
    if tags[0] != tags[1]:
        problems.append("PR slice membership differs from baseline")
    if "seeds" in spec and set(pr.get("manifest", {}).get("seeds", [])) != set(spec["seeds"]):
        problems.append("PR seeds differ from spec")
    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        def ratchet(old_entries, new_entries, key, nested):
            current = {key(m): m for m in new_entries}
            for old in old_entries:
                identity = key(old)
                new = current.get(identity)
                if new is None:
                    problems.append(f"ratchet: removed {identity}")
                    continue
                if old.get("blocking") and not new.get("blocking"):
                    problems.append(f"ratchet: disabled {identity}")
                before = old.get("threshold", {}) if nested else old
                after = new.get("threshold", {}) if nested else new
                for limit in ("min", "max", "max_increase"):
                    if limit in before and (limit not in after or
                            (after[limit] < before[limit] if limit == "min" else after[limit] > before[limit])):
                        problems.append(f"ratchet: loosened {identity}/{limit}")
                if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                    problems.append(f"ratchet: removed CI check for {identity}")
        ratchet(base_spec.get("metrics", []), spec.get("metrics", []), lambda m: m["id"], True)
        ratchet(base_spec.get("slices", []), spec.get("slices", []), lambda m: (m["name"], m["metric"]), False)
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, mid = entry["name"], entry["metric"]
        identity = f"slice:{name}/{mid}"
        a, b = per_item(pr, mid, name), per_item(base, mid, name)
        keys = sorted(a)
        note = ""
        bad = not keys or set(a) != set(b)
        value = sum(a.values()) / len(a) if a else None
        if value is not None and "min" in entry and value < entry["min"]:
            bad = True
        if keys and set(a) == set(b) and entry.get("no_significant_drop"):
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                confidence=bs.get("confidence", 0.95))
            note = f"delta {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            bad |= hi < 0
        if bad and entry.get("blocking"):
            blocked.append(identity)
        verdict = "BLOCK" if bad and entry.get("blocking") else "warn" if bad else "ok"
        lines.append(f"  {identity} {value} {note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
