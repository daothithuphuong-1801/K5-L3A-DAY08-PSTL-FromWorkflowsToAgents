# Judge audit — Nguyễn Vũ Hoàng

MSSV: 2A202603491 · Lớp L3A · Bài cá nhân Lab 9

Bản audit được soạn với hỗ trợ Codex, dựa trên CSV và kết quả chạy script. Chưa có một vòng gắn nhãn độc lập mới; phần này cần được người học đọc và xác nhận trước khi nộp.

FAIL là positive class. Floors: κ ≥ 0,6; precision ≥ 0,8; recall ≥ 0,7; κ không xác định phải fail.

| Tiêu chí | n | TP / FP / FN / TN | κ | Precision | Recall | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 24 / 4 / 6 / 66 | 0,757 | 0,857 | 0,800 | Đạt calibration cho tone |
| helpful | 100 | 9 / 0 / 21 / 70 | 0,375 | 1,000 | 0,300 | Loại khỏi gate |

Rogan–Gladen: tone fail quan sát 0,28 → hiệu chỉnh 0,30; helpful 0,09 → 0,30. Hiệu chỉnh tỷ lệ tổng không sửa được việc bỏ sót từng case. Không sửa verdict CSV để calibration xanh.

## Review bất đồng

Ở phần này, em đối chiếu nội dung reply với nhãn và note công khai. Nhận xét chỉ nằm trong phạm vi dữ liệu đó; nếu note không cho đủ context thì em ghi rõ, không tự đoán thêm thông tin khách hàng.

| Case | Human / judge | Kết luận từ bằng chứng | Sửa rubric đề xuất |
|---|---|---|---|
| H-008 | FAIL / PASS | Đồng ý human: em, nha, anh check quá suồng sã theo chuẩn CS của bộ dữ liệu. | Phân biệt thân thiện và suồng sã; kiểm tra xưng hô. |
| H-017 | FAIL / PASS | Đồng ý human theo chuẩn trong note; tuổi khách không thể suy ra chỉ từ reply. | Dùng anh/chị; rule theo tuổi cần context tuổi cung cấp cho judge. |
| H-029 | FAIL / PASS | Đồng ý human: không cần nhắn thêm mang tính ra lệnh, dù mở đầu bằng Dạ. | Chấm toàn câu; từ lịch sự mở đầu không bù được mệnh lệnh. |
| H-042 | PASS / FAIL | Đồng ý human về tone: ngắn, lịch sự, đủ thông tin thời gian. | Không bắt buộc xin lỗi mọi câu; kiểm tra tiền riêng. |
| H-051 | PASS / FAIL | Đồng ý human theo glossary: refund được cho phép. | Cung cấp glossary; không tự phạt từ tiếng Anh được duyệt. |
| HL-015 | FAIL / PASS | Đồng ý human theo note: reply 55.000, ledger 40.000. | Đưa ledger vào context; kiểm tra tiền bằng code. |
| HL-016 | FAIL / PASS | Đồng ý human theo note: reply 55.000, ledger 35.000; xin lỗi dài không làm tiền đúng. | Factual correctness là điều kiện bắt buộc. |
| HL-020 | FAIL / PASS | Đồng ý human theo note: reply 90.000, ledger 120.000. | So amount được trích xuất với ledger bằng code. |

## Vì sao giữ tone nhưng loại helpful?

Em không chọn helpful làm gate dù precision là 1,0. Con số này có nghĩa các lần nó báo lỗi đều đúng trong tập kiểm tra, nhưng nó chỉ báo được 9 trên 30 lỗi thật. Còn 21 lỗi bị bỏ sót nên dùng nó để chặn bản lỗi sẽ khá nguy hiểm. Recall 0,3 và kappa 0,375 cũng đều chưa đạt yêu cầu đề bài.

Tone đạt cả ba ngưỡng nên có thể dùng cho tiêu chí giọng điệu trong phạm vi bộ dữ liệu này. Tuy nhiên, câu nghe lịch sự không có nghĩa số tiền đúng. Vì vậy tiền và approval vẫn chấm bằng code; gate hiện chưa gọi live judge.

## Điều em chưa kết luận được

Các sửa rubric trong bảng mới là đề xuất. Chưa có lần chạy judge mới trên nhãn held-out nên chưa thể nói sửa xong là judge sẽ tốt hơn. H-017 còn phụ thuộc chuẩn xưng hô trong note; nếu không có context tuổi khách thì không nên tự suy ra tuổi từ câu trả lời. Với các case helpful sai tiền, việc so ledger đáng tin hơn nhận xét chung về độ hữu ích của câu.

Phần Rogan–Gladen cho tỷ lệ hiệu chỉnh 0,30 là kết quả tính trên tập này. Nó không biến những case bị bỏ sót thành đã được bắt, cũng không chứng minh tỷ lệ lỗi khi gặp người dùng thật.

```powershell
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Helpful phải exit 1. Kết quả đầy đủ trong src/reports/lab9_verification.json, sinh bằng python -m lab9.verify. Sửa rubric chỉ là đề xuất, chưa tuyên bố calibration cải thiện khi chưa có held-out mới.
