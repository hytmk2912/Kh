# CHANGELOG — Quyết định và thay đổi

Mỗi dòng: ngày · track · quyết định/thay đổi · lý do. Không xoá dòng cũ; đổi ý thì thêm dòng mới.

- 2026-10-09 · phase0 · Duyệt Giai đoạn 0: nguồn Binance Vision, cửa sổ 2024-10-09 → 2026-10-08, chia 60/20/20 · xem `docs/phase0_report.md`
- 2026-10-10 · ind · Mở track "lướt sóng M1 bằng tổ hợp chỉ báo" theo Prompt 3 (`docs/ind/spec.md`) · gộp Prompt 1 + 2 của chủ repo
- 2026-10-10 · ind · Chọn tổ hợp: lọc theo Bảng A (bắt sóng), chọn cuối theo Bảng B (lãi sau phí, ngoài mẫu) · chủ repo chọn
- 2026-10-10 · ind · Giữ lệnh 1–15 phút; sóng hợp lệ ≥ 0,5% · chủ repo chọn
- 2026-10-10 · ind · M1 vào lệnh, M15 + H1 chỉ lọc hướng · chủ repo chọn; lần chạy bot M1 trước chỉ dùng M1 ra 0 phương pháp
- 2026-10-10 · ind · Nhãn sóng được nhìn lại quá khứ (đáp án), tín hiệu tuyệt đối không · Prompt 2 đúng hơn Prompt 1 ở điểm này
- 2026-10-10 · ind · Dùng chia tập của Giai đoạn 0 (test khoá 2026-05-16 → 2026-10-08), walk-forward train mở rộng ≥ 6 tháng / test 1 tháng · thống nhất với thiết kế đã duyệt
- 2026-10-10 · ind · [A] Backtest baseline TP 0,45% / SL 0,30% / phí taker 0,05%/chiều / trượt 1 tick, cố định cho mọi chỉ báo · giả định ban đầu, chủ repo có thể đổi
- 2026-10-10 · ind · Bảng A tổ hợp yêu cầu precision ≥ 1,5 × ngẫu nhiên trước khi xếp theo recall · chặn lời giải "bắn tín hiệu liên tục"
- 2026-10-09 · ind · Code track ind dùng chung gói `kh` với PR #2 (nhánh `ind-scalp` = `ind-scalp-setup` + merge `phase-0`): tải dữ liệu, chuẩn hoá, engine backtest, công cụ đánh giá · tránh hai bản code trùng và xung đột khi merge
- 2026-10-09 · ind · [A] Nhãn sóng: ưu tiên khi một nến thoả nhiều nhãn UNKNOWN > ĐI NGANG > NHỊP HỒI > SÓNG TĂNG/GIẢM · ZigZag chia toàn bộ chuỗi thành sóng nên cần thứ tự; spec không nêu
- 2026-10-09 · ind · [A] ZigZag không chốt điểm xoay ở cùng nến vừa tạo cực trị mới; sóng nhanh đếm từ nến SAU điểm xuất phát (không biết thứ tự giá trong nến) · thận trọng, tránh nhìn trong nến
- 2026-10-09 · ind · [A] Độ nhạy 0,4% / 0,7%: đổi cùng lúc ngưỡng ZigZag, ngưỡng sóng nhanh và ngưỡng đi ngang; nhịp hồi giữ ZigZag 0,2% · spec chỉ nói "chạy lại với 0,4% và 0,7%"
- 2026-10-09 · ind · Thống kê sóng chỉ tính trên train + validation; nhãn giai đoạn test được lưu (để chấm ở F2) nhưng không mô tả · bảo vệ test khoá
- 2026-10-09 · ind · [A] Quy tắc filter chung: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại); riêng Volume Oscillator > 0, Spread/Ratio |z| > 1, Volume Profile = close ngoài vùng giá trị ngày trước · spec chỉ cho 1 ví dụ (ATR > trung vị 1 ngày)
- 2026-10-09 · ind · [A] Tham số/quy tắc chỉ báo không rõ trong TradingView được chốt trong `registry.py` (mỗi chỗ có nhãn [A] trong phiếu); Zig Zag dùng độ lệch 0,5% thay 5%; Up/Down dùng taker buy/sell của Binance; Envelopes giữ mặc định 10% dù gần như không có tín hiệu trên M1 · chốt trước khi chấm, không chỉnh theo kết quả
- 2026-10-09 · ind · Không triển khai: Volatility Region, Sure Thing (không có công thức chuẩn công bố) · spec §3: có phiếu + lý do, không thay bằng chỉ báo khác
- 2026-10-09 · ind · SuperTrend chép theo quy tắc dải cuối của TradingView (khớp talipp 2,2e-16; pandas-ta dùng thuật toán khác nên chỉ tham khảo); Parabolic SAR theo định nghĩa gốc Wilder (khớp TA-Lib) — bản chép mã Pine từ trí nhớ không kiểm chứng được nên bỏ · đối chiếu I2
- 2026-10-09 · ind · Quy ước số học: MFI = NaN khi cả hai dòng tiền = 0; KAMA ER = 1 khi tổng biến động = 0 (như TA-Lib); thay đổi giá điển hình |Δ| < 1e-10·giá coi là 0 (sai số làm tròn) · khớp TA-Lib, chỉ ảnh hưởng nến filler/giá đứng yên
