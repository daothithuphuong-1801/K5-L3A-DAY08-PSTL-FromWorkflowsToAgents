# Lab 9 — trạng thái và cách chạy

## Đúng thư mục làm bài

Repo Lab 8/Lab 9: `C:\Users\VU-HOANG-DZ\Downloads\K5-L3A-DAY08-PSTL-FromWorkflowsToAgents`.

Remote: `https://github.com/daothithuphuong-1801/K5-L3A-DAY08-PSTL-FromWorkflowsToAgents`.

Nhánh: `starter/d09`; nền Lab 8 `322db9c`. Thư mục P-106 đang mở là dự án khác; không tích hợp overlay vào P-106 và không thay đổi frontend/tài liệu đang làm ở đó.

## Chạy lại trên Windows

Không cần dùng môi trường ảo của P-106 hoặc activate môi trường cũ:

```powershell
cd C:\Users\VU-HOANG-DZ\Downloads\K5-L3A-DAY08-PSTL-FromWorkflowsToAgents\src
.\.venv\Scripts\python.exe -m lab9.verify
```

Máy khác cần tạo môi trường trước:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-lab9.txt
.\.venv\Scripts\python.exe -m lab9.verify
```

Đọc `reports/lab9_verification.json`: 25 bước đạt exit code mong đợi, gồm 47 test Lab 9/Advanced, calibration, baseline v1/v2, gate, detection, mutation, A/A và traps. Report sinh bằng script, không sửa tay. `traps/` chứa report cố ý hỏng để thử gate, không dùng làm baseline.

## Kết quả hiện có

- Core: eval set 14 item sạch; taxonomy 9 FM; audit 8 bất đồng; trace case + regression test; stats/graders hoàn thành; baseline swarm; fixed qua, seeded_regression bị chặn; harness map v1.2; eval card và PRD v1.1.
- Advanced/Expert công khai: eval set v2 28 item sạch; slice gate; pass@k/pass^k; mutation 3/3, 0 báo nhầm; A/A delta 0; bốn trap bị chặn. Không tuyên bố qua test ẩn.
- Metric thêm: `reply_ledger_consistent` bắt FM-08 và `proposal_amount_correct` bắt trajectory bị tự trừ history dù ledger cuối tình cờ đúng.
- Giữ nguyên `src/lab8/`, public world/claims, variant/trap/test công khai của starter. Giữ workflow Lab 8; thêm workflow Lab 9 và bước kiểm chứng nâng cao.

## Lỗi có sẵn của Lab 8

Chạy trên Python 3.13.3:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.pytest-tmp-host
```

Kết quả: **158 passed, 5 xfailed, 1 failed**. Lỗi ở `test_summary_is_recomputed_from_raw_trials[benchmark.json]`: so equality tuyệt đối cho số thực, ví dụ cost `30.390000000000004` so với report cũ `30.390000000000015`.

Đã tái hiện trên worktree nguyên gốc commit `322db9c` không có overlay Lab 9: riêng file test report có 6 passed, 1 failed cùng lỗi. Không chỉnh grader, không sửa tay report hoặc bỏ test để che lỗi. Cần báo giảng viên/chủ repo quyết định cách xử lý tương thích Python; CI host-gate có thể gặp lại lỗi này.

Windows local còn gặp lỗi quyền ở thư mục tạm mặc định của pytest; dùng `--basetemp=.pytest-tmp-host` trong repo để chạy được. Các thư mục tạm này đã được gitignore.

## Việc cá nhân cần xác nhận trước nộp

1. Review audit bằng AI và tự giải thích grader/CI; ghi việc dùng Codex vào báo cáo cá nhân theo RULES.md. Thông tin người nộp: Nguyễn Vũ Hoàng, MSSV 2A202603491, lớp L3A; xem student_info.md và code_explanation.md.
2. Đối chiếu năm anchor nếu lớp có danh sách riêng. Starter chỉ nói key riêng, không cung cấp danh sách/key đó.
3. Người phụ trách bài cá nhân là Nguyễn Vũ Hoàng. Phạm vi hiện chỉ là replay; chưa có phê duyệt pilot thật.
4. Xác nhận repo/đường dẫn nộp bài cá nhân theo lớp; commit trên nhánh riêng, push và mở PR theo hướng dẫn đó; dùng nội dung `docs/lab9_pr_description.md`. Không merge khi chưa có yêu cầu riêng.
5. Đợi GitHub Actions: chưa có bằng chứng CI remote xanh. Baseline mới được sinh ở nhánh khởi tạo; cần được review và bảo vệ làm chuẩn cho các PR tiếp theo.

Tài liệu đề Day 9 nằm ở repo starter, không chép đè README/RUBRIC/SUBMISSION của Lab 8: <https://github.com/VinUni-AI20k/K5-Day9-Evaluation-and-Failure-Analysis>.

## Ổn định SHA giữa Windows và CI

Generator eval set ghi LF cố định để Git không đổi byte CRLF sang LF sau khi đã sinh baseline. Có regression test kiểm tra byte đầu ra; baseline được sinh lại bằng lab9.verify, không sửa tay.
