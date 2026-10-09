# kh — Nghiên cứu định lượng Binance USDⓈ-M Futures

Hệ thống nghiên cứu quy luật giá trên nến 1 phút (BTC, ETH, BNB, SOL, XRP — 730 ngày), từ thu thập dữ liệu
đến khai phá quy luật, mô hình, backtest có chi phí và final test.
**Chỉ phục vụ nghiên cứu/backtest. Không gửi lệnh, không dùng API key Binance.**

Kết quả tổng hợp: [`reports/SUMMARY.md`](reports/SUMMARY.md).

## Chạy trên Google Colab (khuyến nghị)

Mở [`notebooks/kh_colab.ipynb`](notebooks/kh_colab.ipynb) trên Colab (File → Open notebook → GitHub → `hytmk2912/Kh`),
làm theo hướng dẫn ở ô đầu tiên (tạo `GITHUB_TOKEN` trong Colab Secrets), rồi *Runtime → Run all*.
Dữ liệu lưu trên Google Drive (`MyDrive/kh_data`); báo cáo được tự động đẩy lên nhánh `colab-results/<run_id>`.

## Chạy cục bộ

```bash
pip install -e ".[dev]"
export KH_DATA_DIR=/đường/dẫn/kh_data     # mặc định: ./data (không đưa lên Git)
pytest -q                                  # kiểm thử (dữ liệu tổng hợp)
python -m kh.cli all                       # data → quality → waves → features → mine → models → backtest → report
python -m kh.cli final --confirm-final     # final test — CHỈ MỘT LẦN, sau khi commit configs/locked_strategies.yaml
```

| Stage | Việc làm | Đầu ra chính | Thời gian đo được* |
|---|---|---|---|
| `data` | Tải Binance Vision (checksum SHA256, retry, tiếp tục khi gián đoạn), chuẩn hóa Parquet | `$KH_DATA_DIR/raw`, `normalized` | ~14 phút |
| `quality` | Kiểm tra nến thiếu/trùng/OHLC/filler, đối chiếu file tháng với file ngày | `reports/data_quality/` | ~25 giây |
| `waves` | Phát hiện sóng DC/ZigZag đa thang, thống kê, H1 | `reports/waves/` | ~20 giây |
| `features` | 75 đặc trưng causal + nhãn triple-barrier, lấy mẫu 15 phút | `$KH_DATA_DIR/work/features` | ~3 phút |
| `mine` | Giả thuyết H2–H7, quét 900 kiểm định có FDR, tổ hợp, decile, chế độ thị trường | `reports/patterns/` | ~3 phút |
| `models` | Logistic + LightGBM walk-forward có purge/embargo, leave-one-coin-out | `reports/models/` | ~10 phút |
| `backtest` | 14 biến thể chiến lược, baseline, độ bền, DSR, PBO → khóa lựa chọn | `reports/backtest/`, `configs/locked_strategies.yaml` | |
| `final` | Final test một lần | `reports/final_test/` | |
| `report` | Tổng hợp | `reports/SUMMARY.md` | |

\*Đo trong container cloud 4 CPU; Colab có thể khác.

## Cấu trúc

```
configs/default.yaml        cấu hình (symbol, cửa sổ, chia tập, phí, tham số)
configs/locked_strategies.yaml  lựa chọn đã khóa trước final test
docs/                       báo cáo giai đoạn 0, đăng ký giả thuyết, danh mục đặc trưng
src/kh/data                 tải, chuẩn hóa, kiểm tra chất lượng
src/kh/waves                Directional Change / ZigZag, báo cáo sóng
src/kh/features             đặc trưng causal, chế độ thị trường
src/kh/labels               nhãn triple-barrier
src/kh/patterns             thống kê, quét quy luật, FDR
src/kh/models               walk-forward
src/kh/backtest             engine, chiến lược, nghiên cứu backtest
src/kh/evaluation           chỉ số, DSR/PBO, final test, tổng kết
src/kh/tracking             registry thí nghiệm
tests/                      pytest (gồm test chống look-ahead)
notebooks/kh_colab.ipynb    chạy trên Colab + tự đẩy kết quả lên GitHub
```

## Nguyên tắc

- Dữ liệu lớn không đưa lên Git; mọi thí nghiệm được ghi ở `reports/experiments/registry.csv`.
- Giả thuyết và tiêu chí được đăng ký trước: [`docs/hypotheses.md`](docs/hypotheses.md) (kèm nhật ký thay đổi phương pháp).
- Đặc trưng tại t chỉ dùng dữ liệu có sẵn khi nến t đóng cửa; vào lệnh ở giá mở cửa nến t+1.
- Kết quả backtest không phải lợi nhuận thực tế.
