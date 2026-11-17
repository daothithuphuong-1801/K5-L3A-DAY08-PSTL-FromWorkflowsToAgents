# Eval card — LogiX-VN refund agent

## Phiên bản và provenance

- Lab 8 gốc: commit 322db9c061ed921287e481d0778099dc485cd32e; không sửa src/lab8/.
- Starter Day 9: https://github.com/VinUni-AI20k/K5-Day9-Evaluation-and-Failure-Analysis, commit d1b9471540727d693c9eb392667b9f0d8a998bf5.
- Nhánh triển khai: starter/d09. Dấu vết code/grader/spec: source SHA-256 `4fdae5a05a94f40bffd7d9a8efb3f0577897ea34df9c9951cafdccc90989d17d` trong reports/lab9_verification.json.
- v1: eval SHA `cab584e577b5`; 14 item × 5 seed (11,22,33,44,55); nhãn riêng labels_v1.json; metric spec 1.0.
- Run baseline: `E-swarm-20261117-cab5`; fixed `E-fixed-20261117-cab5`; regression `E-seeded_regression-20261117-cab5`.
- Python 3.13.3; MockLLM; pydantic-evals 2.68.0. Cost là mô phỏng, không phải giá API.

## Kết quả Core

| Metric | Baseline swarm | Fixed | Seeded regression |
|---|---|---|---|
| approval_bypass | 0 | 0 | 0 |
| secret_leak | 0 | 0 | 0 |
| db_fact_kept | 0.9857 | 1.0 | 0.9286 |
| refund_amount_correct | 0.9857 | 1.0 | 0.8571 |
| pass_rate | 0.9857 | 1.0 | 0.7143 |
| reply_ledger_consistent | 1.0 | 1.0 | 0.7857 |
| proposal_amount_correct | 0.9857 | 1.0 | 0.7857 |
| pass_5 | 0.9286 | 1.0 | 0.7143 |
| cost_per_success | 49.567 | 48.7157 | 81.202 |

Paired bootstrap theo mean mỗi item qua 5 seed, không coi 70 trial độc lập. 1.000 resample percentile, RNG 2027, CI 95%. Pass rate Δ(PR−baseline) = −0,271; CI [−0,500; −0,057] nên chặn. Fixed exit 0; regression exit 1. Safety dùng số vi phạm, không lấy trung bình để che lỗi.

Detection 100%, false alarm 0% trên variant công khai (lab9.mutation --detect). Thêm proposal_amount_correct để bắt cả C-013 pre_deducted có ledger 0 đúng nhưng proposal sai.

## Judge và trace

Tone: κ=0,757, P=0,857, R=0,800, đạt floors. Helpful: κ=0,375, P=1,0, R=0,3, loại. Xem judge_audit.md; bản audit có hỗ trợ AI, người nộp bài cần đọc và xác nhận lại. Gate chấm tiền và approval bằng code.

Trace case: [trace_case.md](trace_case.md), C-002@11 event 3 model_override; có regression test fail trên variant lỗi và pass trên fixed.

## v2 — slices, reliability và integrity

- Baseline `E-swarm-20261117-0c56`, SHA `0c56cc4127ce`; 28 item × 5 seed, gồm 14 item adversarial; labels_v2.json riêng.
- pass_hat_5 baseline=0.8929; sàn blocking 0,8. Hai bộ seed A/A cho Δ=0 ở mọi metric: quan sát này không phải ước lượng độ nhiễu cho LLM thật. Chọn 0,8 thấp hơn baseline 0,8929 với khoảng đệm 0,0929; phải đo lại trên dữ liệu mới trước pilot thật.
- money_movement, adversarial và denial đều blocking ở min 0,90, kiểm tra thêm CI giảm.
- slice_regression bị chặn bởi money_movement dù pass_rate toàn cục qua sàn.
- flaky_regression bị chặn bởi pass_hat_5 (và các metric khác); không phụ thuộc event model_override nên áp dụng được với quiet_override.
- Integrity kiểm tra số dòng, tích item×seed, dòng trùng, seeds, slice tags, giá trị hữu hạn, lỗi grader và aggregate khớp raw rows. Ratchet cần --base-spec lấy từ revision baseline tin cậy.

```text
fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, reply_ledger_consistent, pass_hat_5, proposal_amount_correct, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          proposal_amount_correct, slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, proposal_amount_correct, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

Cả 4 trap công khai exit 1, lý do INTEGRITY/ratchet. Baseline so với chính nó exit 0. Test bổ sung bao gồm dòng trùng và evaluator_failures trên run xanh.

## Người phụ trách và pilot

Người phụ trách evaluation trong bài cá nhân: Nguyễn Vũ Hoàng — 2A202603491, lớp L3A. Pilot hiện chỉ là replay offline trên dữ liệu LogiX-VN giả lập. Chưa có phê duyệt triển khai cho khách hàng thật.

## Giới hạn

- MockLLM, 14/28 item và judge replay công khai; chưa có held-out độc lập hoặc đo người dùng thật.
- Không có key anchor/test ẩn của giảng viên. Không suy từ test công khai sang bảo đảm đủ điểm.
- FM-08 đọc số tiền có currency suffix trong event reply; không phải bộ hiểu mọi cách diễn đạt tiền bằng chữ. Swarm Lab 8 không có reply event nên metric trả pass như not-applicable, chưa chứng minh chất lượng reply của swarm. Lab 9 resolved mà mất reply sẽ fail.
- Bug rare bật khi seed chia hết 3 (xác suất khoảng 1/3 nếu lấy seed đều); chỉ có 5 seed nên không phát hiện ổn định. Không hạ sàn để khớp variant.
- Ratchet là so sánh policy; cần branch protection, baseline/spec từ nhánh tin cậy để chống sửa đồng thời evaluator và baseline. Không xem baseline sinh trên nhánh mới là artifact đã được bảo vệ.
- Host suite Lab 8 trên Python 3.13 có một lỗi có sẵn do equality số thực; xem lab9_status.md. CI GitHub chưa chạy.

## Đổi phiên bản

Thêm/đổi item hoặc nhãn → tăng eval_set_version và sinh baseline mới. Đổi metric/ngưỡng → tăng metric_spec_version, giải thích trong PRD; cùng eval-set không được nới protection. Khi thay code/grader/spec chạy lại python -m lab9.verify và cập nhật card từ report mới.
