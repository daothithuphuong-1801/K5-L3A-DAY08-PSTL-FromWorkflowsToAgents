# Day 9: evaluation, failure analysis và regression gate

Bổ sung overlay Day 9 lên Lab 8 commit 322db9c, giữ nguyên src/lab8/. Grader kiểm tra approval, ledger, proposal, reply; paired bootstrap/gate chặn regression. v2 thêm adversarial slices, pass^k và integrity/ratchet.

## Kiểm chứng local

```text
..............................................                           [100%]
47 passed, 412 deselected in 4.40s
```

25/25 bước trong python -m lab9.verify đạt exit code mong đợi. Helpful exit 1 là đúng vì calibration fail.

```text
gate: PR E-seeded_regression-20261117-cab5 vs main E-swarm-20261117-cab5 · eval set cab584e577b5
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_ledger_consistent 0.7857   {"min": 1.0}                                                          BLOCK
  proposal_amount_correct 0.7857   {"min": 0.95}                                                         BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_ledger_consistent, proposal_amount_correct
```

```text
fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, reply_ledger_consistent, pass_hat_5, proposal_amount_correct, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          proposal_amount_correct, slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, proposal_amount_correct, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

A/A giữa 11,22,33,44,55 và 66,77,88,99,110: delta 0 trên mọi metric. Các trap:

```text
exit 1 — blocked: integrity [reports/traps/evaluator_errors_as_nan.json]
exit 1 — blocked: integrity [reports/traps/dropped_failing_rows.json]
exit 1 — blocked: integrity [reports/traps/cherry_picked_seeds.json]
exit 1 — blocked: integrity [reports/traps/loosened_spec.json]
```

## Giới hạn cần review trước nộp

- CI GitHub chưa chạy; chưa tuyên bố hai job eval-gate xanh.
- Host suite Lab 8: 158 passed, 5 xfailed, 1 failed do equality số thực trong benchmark cũ trên Python 3.13. Tái hiện cùng lỗi trên worktree nguyên gốc 322db9c; không sửa Lab 8 hoặc report cũ.
- Người nộp: Nguyễn Vũ Hoàng — 2A202603491, L3A. Audit có hỗ trợ AI cần được người học review; chưa có key anchor/test ẩn hoặc phê duyệt pilot thật.
- Không merge PR nếu chưa được yêu cầu riêng.

Tài liệu: docs/eval_card.md, docs/PRD_v1.1.md, docs/failure_taxonomy.md, docs/judge_audit.md, docs/trace_case.md. Nguồn: starter Day 9 của VinUni-AI20k, commit d1b9471. Code có hỗ trợ Codex; người nộp cần ghi usage vào báo cáo cá nhân theo RULES.md.
