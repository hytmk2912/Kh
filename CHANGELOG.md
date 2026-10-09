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
