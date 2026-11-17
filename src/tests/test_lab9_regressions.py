"""Exercise actual failing traces and report tampering, not variant-name checks."""
import copy
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(autouse=True)
def lab9_modules():
    # Lab 8 CI collects student tests with only its own dependencies installed.
    from lab9 import gate, stats
    from lab9.graders import DbFactKept, RefundAmountCorrect, ReplyLedgerConsistent
    from lab9.trace_case import investigate
    globals().update(gate=gate, stats=stats, DbFactKept=DbFactKept,
                     RefundAmountCorrect=RefundAmountCorrect,
                     ReplyLedgerConsistent=ReplyLedgerConsistent, investigate=investigate)


def context(trial, label):
    return SimpleNamespace(output=trial, expected_output=label)


def test_lab9_evalset_hash_is_stable_after_git_line_normalization(tmp_path, monkeypatch):
    from lab9 import evalset
    items, labels = tmp_path / "items.jsonl", tmp_path / "labels.json"
    monkeypatch.setattr(evalset, "ITEMS", items)
    monkeypatch.setattr(evalset, "LABELS", labels)
    evalset.build()
    assert b"\r" not in items.read_bytes()


def test_lab9_first_wrong_step_ticket_overrides_database():
    bad = investigate("seeded_regression", "C-002", 11)
    fixed = investigate("fixed", "C-002", 11)
    assert bad["trial"]["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    for case, expected in ((bad, False), (fixed, True)):
        ctx = context(case["trial"], case["label"])
        assert DbFactKept().evaluate(ctx).value is expected
        assert RefundAmountCorrect().evaluate(ctx).value is expected


@pytest.mark.parametrize("text,ledger,ok", [
    ("Đã hoàn 120.000đ cho đơn O-515.", 120000, True),
    ("Đã hoàn phí 120,000 VND cho đơn O-515 ạ.", 120000, True),
    ("Đã hoàn 120 000 đồng, tiền về trong 3–5 ngày.", 120000, True),
    ("Đã hoàn 150.000đ cho đơn O-515.", 120000, False),
    ("Đã hoàn 35.000đ.", 0, False),
    ("Đã hoàn cho đơn O-515.", 120000, False),
])
def test_lab9_reply_metric_checks_money_without_matching_template(text, ledger, ok):
    trial = {"events": [{"kind": "reply", "payload": {"text": text}}],
             "result": {"status": "resolved"}, "snapshot": {"refund_vnd": ledger}}
    assert ReplyLedgerConsistent().evaluate(context(trial, {})).value is ok


def clean_report():
    return {"manifest": {"items": 2, "seeds": [11, 22], "eval_set_sha": "x"},
            "rows": [{"item_id": i, "seed": s, "pass_rate": True, "slices": ["money_movement"]}
                     for i in ("a", "b") for s in (11, 22)],
            "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}


SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "blocking": True,
        "threshold": {"min": 0.8, "no_significant_drop": True}}],
        "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.9, "blocking": True}]}


@pytest.mark.parametrize("attack", ["duplicate", "failure", "null", "slices", "aggregate"])
def test_lab9_advanced_integrity_rejects_forged_evidence(attack):
    base = clean_report()
    pr = copy.deepcopy(base)
    if attack == "duplicate":
        pr["rows"][0] = copy.deepcopy(pr["rows"][1])
    elif attack == "failure":
        pr["evaluator_failures"] = ["grader crashed on an otherwise green run"]
    elif attack == "null":
        pr["rows"][0]["pass_rate"] = None
    elif attack == "slices":
        for row in pr["rows"]:
            row["slices"] = []
    elif attack == "aggregate":
        pr["rows"][0]["pass_rate"] = False
    assert gate.integrity_check(pr, base, SPEC)
    assert gate.integrity_check(base, base, SPEC) == []


@pytest.mark.parametrize("attack", ["metric", "slice", "ci", "blocking"])
def test_lab9_advanced_ratchet_rejects_removed_protections(attack):
    spec = copy.deepcopy(SPEC)
    if attack == "metric":
        spec["metrics"] = []
    elif attack == "slice":
        spec["slices"] = []
    elif attack == "ci":
        spec["metrics"][0]["threshold"].pop("no_significant_drop")
    else:
        spec["metrics"][0]["blocking"] = False
    base = clean_report()
    assert gate.integrity_check(base, base, spec, SPEC)


@pytest.mark.parametrize("args", [(0, 0, 1), (5, -1, 1), (5, 6, 1), (5, 2, 0),
                                 (5, 2, 6), (5.0, 2, 1), (True, 1, 1)])
def test_lab9_advanced_both_estimators_reject_invalid_arguments(args):
    for fn in (stats.pass_at_k, stats.pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)
