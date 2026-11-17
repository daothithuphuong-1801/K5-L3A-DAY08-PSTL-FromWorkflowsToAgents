# Trace case — ticket ghi đè dữ kiện DB

| Trường | Bằng chứng |
|---|---|
| Trial | seeded_regression C-002@11; report E-seeded_regression-20261117-cab5; result R-seeded_regression-C-002-s11 |
| Triệu chứng | Status resolved thay vì denied; ledger 20.000đ / 1 dòng thay vì 0đ / 0 dòng. |
| Bước sai đầu tiên | Event **3**, model_override, payload {delay_days: 5}. |
| Vì sao là đầu tiên | Event 1 handoff đúng phạm vi; event 2 investigator đọc DB. Event 3 mới thay delay bằng ticket. Event 4 quote 20.000 và event 6 reply là hậu quả. |
| Failure mode | FM-03. Không gắn FM-08 cho case này: reply 20.000 khớp ledger 20.000, dù quyết định hoàn sai. |
| Đối chứng | fixed C-002@11: event 3 quote amount_vnd=0, reason=no_entitlement; event 4 reply từ chối; ledger 0. |
| Regression test | tests/test_lab9_regressions.py::test_lab9_first_wrong_step_ticket_overrides_database kiểm tra event 3; DbFactKept và RefundAmountCorrect false trên lỗi, true trên fixed. |
| Chưa chắc chắn | Trace chỉ chứng minh event sai đầu tiên được ghi, không chứng minh toàn bộ suy luận nội bộ. MockLLM không đại diện model thật. |

Tái tạo từ src:

```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= -k lab9_first_wrong_step
```

C-013 với pre_deducted có ledger 0 đúng nhãn nhưng proposal 0 sai nhãn 35.000: shape tự trừ history rồi bỏ qua host. ProposalAmountCorrect bắt được lỗi này khi grader chỉ nhìn ledger không bắt được.
