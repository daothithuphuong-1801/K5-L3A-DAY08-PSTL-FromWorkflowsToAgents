# Giải thích code Lab 9 — Nguyễn Vũ Hoàng

MSSV: 2A202603491 · Lớp L3A

Bản giải thích này được soạn với hỗ trợ Codex, dựa vào code và kết quả chạy thực tế. Các phần cần đọc thêm được ghi riêng ở cuối; không cố tình thêm lỗi hoặc khẳng định đã hiểu hết lý thuyết.

## 1. Bài này đang kiểm tra điều gì?

Cách hiểu ngắn gọn là agent chạy được chưa đủ. Khi đổi một phiên bản, cần kiểm tra nó có hoàn tiền đúng, có vượt approval hay nói sai số tiền không. Vì vậy phần Lab 9 giữ nguyên agent Lab 8, rồi thêm bộ câu hỏi, grader và gate ở bên ngoài.

Luồng chính là: tạo eval set → chạy từng claim với các seed → chấm từng trial → tổng hợp report → so với baseline. Các file JSON trong reports được sinh bằng lệnh, không điền kết quả bằng tay.

## 2. evalset.py — tách đề và đáp án

File eval_set_v1.jsonl chứa item, claim_id, failure_modes và provenance. Đáp án như số tiền đúng nằm riêng trong labels_v1.json. Khi chạy, harness lấy claim từ world và chuyển nhãn cho grader; câu trả lời của agent không được dùng làm đáp án.

PUBLIC_MODES gắn FM theo rủi ro mà từng case kiểm tra. Ví dụ C-002 kiểm tra FM-03 vì ticket và DB có thể khác số ngày trễ. Gắn FM không có nghĩa case đó luôn fail: cùng case chạy fixed vẫn có thể đúng.

v2 giữ các item v1 và thêm pack adversarial. fm_map.yaml nối cơ chế tấn công với mã FM. Slice money_movement lấy theo nhãn hoàn tiền dương, không lấy theo việc agent có chịu hoàn hay không. Nếu lấy theo output thì agent có thể làm một case khó biến mất khỏi slice bằng cách từ chối nó.

## 3. graders.py — đọc ledger trước khi tin lời trả lời

### ApprovalBypass

Grader này trả true khi có tiền ghi mà nhãn nói approval không hợp lệ, hoặc có dòng ledger dưới claim khác. Với metric này true là có lỗi, nên ngưỡng là max=0. Điểm dễ nhầm là các metric capability lại dùng true để biểu thị đúng.

Host từ chối nhưng agent nói đã hoàn chưa đồng nghĩa tiền thật đã chuyển. Trường hợp đó cần TrialPass và grader reply, không đổi ý nghĩa ApprovalBypass để bắt cả hai.

### RefundAmountCorrect

Chỉ so snapshot.refund_vnd với nhãn refund_vnd. Nó không đọc câu trả lời để quyết định tiền có đúng không. Một reply lịch sự vẫn có thể đi kèm ledger sai.

### ProposalAmountCorrect

Grader này so proposal_amount với nhãn. Nó được thêm vì C-013 có thể có ledger 0 đúng nhưng quá trình xử lý sai: shape tự trừ history, đưa proposal về 0 và không đi qua quyết định host như mong đợi.

Ở C-014, quote đầy đủ là 150.000 và đã hoàn trước đó 30.000. Shape phải gửi 150.000 cho host, host mới trả thêm 120.000. Nếu shape tự gửi 120.000, host trừ tiếp 30.000 thì chỉ còn 90.000. Đây là lỗi trừ hai lần.

### ReplyLedgerConsistent

Grader tìm các số có đơn vị tiền như đ, đồng hoặc VND trong event reply rồi so với ledger của claim. Ví dụ reply nói 150.000đ nhưng ledger 120.000 thì fail. Regex không cần câu trả lời giống nguyên mẫu, nên honest_refactor đổi cách diễn đạt vẫn qua.

Giới hạn là nó chưa hiểu mọi cách viết tiền bằng chữ hoặc câu phức tạp. Swarm Lab 8 không có event reply nên được xem là không áp dụng và trả pass. Điều này chưa chứng minh reply của swarm tốt; chỉ tránh sửa Lab 8 để thêm event. Với trial Lab 9 resolved mà mất reply, grader sẽ fail.

### DbFactKept

Grader tìm event model_override. C-002 của seeded_regression có event thứ 3 ghi delay_days=5 từ ticket thay cho DB. Tuy vậy nếu agent ghi sai nhưng không phát event này thì riêng DbFactKept không bắt được. Vì thế vẫn cần grader proposal, ledger và pass_rate.

## 4. stats.py — vì sao không chỉ nhìn accuracy?

Trong calibration, FAIL là positive class vì mục tiêu là tìm lỗi. TP là lỗi thật và judge cũng báo lỗi; FN là lỗi thật bị judge bỏ sót.

Precision = TP/(TP+FP): trong những case judge báo lỗi, bao nhiêu case đúng là lỗi. Recall = TP/(TP+FN): trong toàn bộ lỗi thật, judge tìm được bao nhiêu. Helpful có precision 1,0 nhưng recall 0,3, tức chỉ bắt được 9/30 lỗi. Vì vậy không chọn nó làm gate.

Cohen kappa có trừ phần đồng ý có thể xảy ra do tỷ lệ nhãn. Nếu mẫu số bằng 0 thì code báo ValueError và calibration không được coi là đạt. Chưa nên diễn giải kappa như một bảo đảm đúng cho mọi dữ liệu mới.

Rogan–Gladen hiệu chỉnh tỷ lệ lỗi quan sát theo sensitivity và specificity. Công thức là (p_obs + specificity − 1)/(sensitivity + specificity − 1), sau đó chặn về [0,1]. Nó sửa ước lượng tỷ lệ tổng, không sửa verdict từng case. Nếu mẫu số không dương thì code không tiếp tục hiệu chỉnh.

## 5. paired_bootstrap — so hai bản trên cùng item

Mỗi item chạy 5 seed rồi lấy mean. Hai vector PR và baseline phải cùng item, cùng thứ tự. scipy bootstrap lấy mẫu cặp tương ứng để giữ việc so cùng tình huống; không lấy mẫu độc lập hai bên.

Hàm trả delta = PR − baseline và CI 95%. Nếu cả CI nằm dưới 0 thì có bằng chứng giảm theo phép kiểm này. Seeded regression có delta pass_rate khoảng −0,271, CI [−0,500; −0,057], nên bị chặn.

CI chạm hoặc chứa 0 không chứng minh hai bản bằng nhau. Nó chỉ chưa chỉ ra được mức giảm rõ theo tiêu chí này; các sàn tuyệt đối và metric safety vẫn được kiểm tra riêng.

## 6. gate.py — quyết định cho qua hay chặn

Gate kiểm tra eval-set SHA rồi kiểm tra integrity trước khi so điểm. Nếu report thiếu dòng, trùng item×seed, đổi seed, đổi slice, có NaN/None hoặc grader crash thì không nên đem các số trung bình đó so với baseline.

Gate cũng tính lại aggregate từ rows để tránh trường hợp bảng tổng nhìn đẹp nhưng bằng chứng bên dưới khác. Sau đó mới kiểm tra max/min, mức tăng cost và CI. Chỉ metric blocking mới khiến gate chặn; metric theo dõi vẫn có thể in cảnh báo.

slice_check làm tương tự trên các nhóm item. Slice regression có thể nhỏ khi nhìn toàn bộ tập nhưng lớn trong nhóm có chuyển tiền. Money_movement giúp nhìn đúng phần này.

Ratchet so spec hiện tại với base-spec: cùng eval-set version thì không được hạ min, tăng max, bỏ metric/slice, tắt blocking hoặc bỏ điều kiện CI. Base-spec phải lấy từ revision tin cậy. Nếu lấy luôn file vừa sửa trong PR làm chuẩn thì kiểm tra này mất ý nghĩa.

## 7. pass@k và pass^k khác nhau thế nào?

pass@k là xác suất có ít nhất một lần thành công khi chọn k lần từ n lần đã chạy. pass^k là xác suất cả k lần đều thành công. Code dùng tổ hợp, không lấy pass_rate rồi nhân tùy ý.

Ví dụ 5 lần chạy có 4 lần đúng: pass@5=1 nhưng pass^5=0. Agent có thể làm đúng ít nhất một lần nhưng chưa ổn định qua cả năm lần. Vì thế pass_hat_5 được dùng để bắt lỗi chập chờn.

Các đầu vào không hợp lệ như c>n, k=0, k>n hoặc số không nguyên sẽ bị từ chối. Cần phân biệt pass^5 trên một tập chạy với kết luận độ tin cậy trên người dùng thật.

## 8. Kết quả nào đã kiểm chứng?

- 47 test Lab 9/Advanced qua; 25 bước trong lab9.verify đạt exit code mong đợi.
- Fixed được qua, seeded_regression bị chặn.
- Mutation 3/3 regression bị chặn, không báo nhầm trên fixed/honest_refactor.
- Bốn trap công khai bị chặn; hai bộ seed A/A cho delta 0.
- Lab 8 vẫn có một lỗi test report số thực trên Python 3.13, tái hiện cả ở commit gốc. Không sửa Lab 8 để làm test này xanh.

## 9. Những điểm còn phải kiểm tra thêm

Cần đọc thêm cách chọn ngưỡng khi LLM thật có noise, cách thay đổi cỡ mẫu ảnh hưởng CI và độ bao phủ của regex tiền. A/A delta 0 trên MockLLM không đủ để chọn ngưỡng cho production. Chưa có key anchor/test ẩn hoặc dữ liệu người dùng thật.

Trước khi nộp cần đọc lại các nhận xét audit, chạy được một trace đối chứng và tự giải thích các điểm trên. Test xanh là bằng chứng hành vi trên các case đã chạy, không thay cho việc hiểu code.
