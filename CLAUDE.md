# CLAUDE.md — Quy tắc vận hành repo Kh

Repo nghiên cứu định lượng Binance USDⓈ-M Perpetual, nến 1 phút. Chỉ nghiên cứu, **không giao dịch thật**.
Người duyệt: chủ repo (hytmk2912). Trả lời và viết tài liệu bằng **tiếng Việt đơn giản**, định nghĩa thuật ngữ khi dùng lần đầu.

## Track đang chạy

| Track | Nhánh | Việc | Đặc tả | Trạng thái |
|---|---|---|---|---|
| M1 — lướt sóng 1–15 phút | `ind-scalp` | `TASKS.md` | `docs/ind/spec.md` | đóng: không tổ hợp nào lãi sau phí |
| **M15 — vào lệnh khung M15** | **`ind15`** | **`TASKS_M15.md`** | **`docs/ind15/spec.md`** | **đang làm** |

Mặc định làm track đang chạy. Code dùng chung; đổi code M1 thì kết quả M1 đã commit phải giữ nguyên.

## Đọc gì trước khi làm

1. File việc của track đang chạy — việc đang dở và điều kiện "xong" của từng việc. **Luôn bắt đầu từ việc `[ ]` đầu tiên.**
2. Đặc tả của track đang chạy.
3. `CHANGELOG.md` — các quyết định đã chốt. Không làm ngược quyết định đã ghi.
4. `docs/phase0_report.md` + `reports/phase0/` — sự thật đã đo về nguồn dữ liệu (Giai đoạn 0, đã duyệt).

## Sự thật đã đo (đừng kiểm tra lại từ đầu, chỉ xác minh khi tải)

- REST `fapi.binance.com` trả **HTTP 451** từ container cloud → không gọi REST, không gọi exchangeInfo.
- Nguồn dữ liệu: `https://data.binance.vision` (liệt kê qua `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=...`).
  - Klines 1m: `data/futures/um/monthly/klines/{SYM}/1m/{SYM}-1m-{YYYY-MM}.zip` (2024-10 → 2026-09) + `data/futures/um/daily/klines/{SYM}/1m/{SYM}-1m-{YYYY-MM-DD}.zip` (2026-10-01 → 2026-10-08). Mỗi zip có file `.CHECKSUM` (SHA256).
  - Funding: `data/futures/um/monthly/fundingRate/{SYM}/` (chu kỳ 8h).
- Cửa sổ cố định: **2024-10-09 00:00 → 2026-10-08 23:59 UTC**, mỗi symbol đúng **1.051.200** nến, 0 thiếu, 0 trùng.
- Nến "filler" (volume = 0 và O=H=L=C, lúc sàn bảo trì): BTC 126, ETH 127, BNB 128, SOL 128, XRP 127. **Giữ nguyên, gắn cờ `is_filler`, không nội suy, không vào lệnh.**
- Không có spread bid/ask lịch sử trong cửa sổ → trượt giá là **giả định**, phải ghi rõ.
- Cột CSV có header: `open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore` (timestamp ms).
- Tải toàn bộ klines 5 symbol ≈ 215 MB zip, ≈ 1 phút. Có lỗi SSL tạm thời → luôn retry (2, 4, 8, 16 s; tối đa 5 lần).

## Nguyên tắc bắt buộc

1. **Không bịa số.** Ô chưa có kết quả để trống. Không thay dữ liệu thật bằng dữ liệu mô phỏng.
2. **Không nhìn tương lai.** Tín hiệu tại nến t chỉ dùng dữ liệu đến hết nến t đã đóng; vào lệnh ở giá mở nến t+1. Nến M15/H1 chỉ dùng khi đã đóng.
3. **Nhãn sóng (đáp án) không bao giờ là đầu vào của tín hiệu.** Module tín hiệu không được import module nhãn — có test kiểm tra.
4. **Tập test cuối bị khoá** (2026-05-16 → 2026-10-08). Chỉ chạy một lần ở việc cuối của TASKS.md. Không chỉnh gì sau khi xem nó.
5. **Mỗi số liệu gắn nhãn:** [F] đã đo · [A] giả định · [I] suy luận · [L] giới hạn.
6. Mọi thay đổi tham số, nhãn, quy tắc, tiêu chí → ghi 1 dòng vào `CHANGELOG.md` (ngày, thay đổi, lý do).
7. Mọi lần chạy thử tổ hợp/tham số được đếm trong `reports/<track>/trials.csv` (`ind` hoặc `ind15`) (để tính multiple testing).

## Cách làm việc

- **Tự làm** mọi bước đã rõ trong TASKS.md, không hỏi từng thao tác. Xong việc này thì làm tiếp việc sau.
- **Dừng và hỏi** khi: đổi phạm vi (symbol, cửa sổ, ngưỡng sóng 0,5%, giữ lệnh ≤ 15 phút, phí); mở tập test cuối; xoá dữ liệu/nhánh/lịch sử; force push; bất cứ thứ gì tốn tiền.
- **Chỉ đánh dấu `[x]`** khi lệnh kiểm tra ở cột "Xong khi" chạy qua và kết quả được dán vào `TASKS.md` (dòng log ngắn: lệnh + con số). Không có bằng chứng = chưa xong.
- Cuối mỗi việc: cập nhật `TASKS.md` (trạng thái + log + ghi chú phiên), commit, push. Container bị xoá khi hết phiên — cái gì không commit là mất.
- Khi ngữ cảnh sắp đầy hoặc phiên mới: đọc lại `TASKS.md` mục "Ghi chú phiên" rồi làm tiếp.

## Git

- Làm trên nhánh của track đang chạy (bảng ở đầu file), commit theo từng việc, mở 1 PR cho mỗi track và cập nhật dần. Không tự merge vào `master`.
- Chỉ commit file nhỏ: code, test, tài liệu, `reports/ind/**`, `reports/ind15/**` (csv/json/md/png, mỗi file < 5 MB). `data/` đã nằm trong `.gitignore`.
- Commit message tiếng Việt, ngắn, dạng `ind: <việc> — <kết quả chính>`.

## Môi trường

- Python ≥ 3.10, `pandas`, `numpy`, `pyarrow`, `numba` (nếu cần cho vòng lặp đệ quy), `pytest`. Khoá phiên bản trong `requirements.txt`.
- Được phép `pip install`. **Không dùng API trả phí, không đề xuất VPS.**
- Xử lý **từng symbol một**, dùng `float32` cho chỉ báo/tín hiệu, lưu trung gian Parquet trong `data/` (không commit).
- Phiên mới: chạy lại bước tải — manifest bỏ qua file đã xác minh SHA256.
- Nếu container thiếu RAM/thời gian cho một bước: tạo notebook Colab mỏng trong `notebooks/` (chỉ gọi `src/`), ghi rõ trong TASKS.md bước nào cần chạy trên Colab, rồi làm tiếp phần chạy được.

## Cấu trúc code (track lướt sóng chỉ báo)

```
src/kh/data/        tải Binance Vision, manifest, chuẩn hoá Parquet, kiểm chất lượng, resample M15/H1
src/kh/ind/labels.py      ZigZag 0,5% → sóng, nhịp hồi, đi ngang (đáp án)
src/kh/ind/indicators/    mỗi chỉ báo 1 hàm + metadata trong registry.py
src/kh/ind/signals.py     chỉ báo → sự kiện Long/Short, bộ lọc khung lớn
src/kh/ind/score.py       Bảng A (bắt sóng)
src/kh/backtest/          mô phỏng lệnh, phí, trượt giá, funding
src/kh/ind/combos.py      quét tổ hợp 2–4
src/kh/evaluation/        walk-forward, purge/embargo, bootstrap, DSR, PBO
src/kh/ind/report.py      xuất bảng vào reports/ind/
tests/                    pytest, gồm test chống nhìn tương lai
```

Chạy: `pip install -e .` rồi `python -m kh.ind <bước>` (track M1) hoặc `python -m kh.ind15 <bước>` (track M15) (bước = `data`, `labels`, `indicators`, `single`, `combos`, `final`).
