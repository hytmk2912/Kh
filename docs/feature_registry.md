# Danh mục đặc trưng (feature registry)

Tất cả đặc trưng tại nến t dùng dữ liệu có sẵn khi nến t đóng cửa. σ = σ_1m EWMA (halflife 1 ngày) dịch 1 nến.
Metrics (OI, long/short) chỉ dùng từ create_time + 5 phút. Funding dùng giá trị đã thanh toán gần nhất.
Đã kiểm tra bằng test cắt cụt (`tests/test_lookahead.py`).

| Tên | Nhóm | Công thức | Đơn vị | Nguồn | Thời điểm khả dụng |
|---|---|---|---|---|---|
| `ret_5_z` | A_price | log(c_t/c_(t-5)) / (σ·√5) | z | klines_1m | đóng cửa nến t |
| `ret_15_z` | A_price | log(c_t/c_(t-15)) / (σ·√15) | z | klines_1m | đóng cửa nến t |
| `ret_30_z` | A_price | log(c_t/c_(t-30)) / (σ·√30) | z | klines_1m | đóng cửa nến t |
| `ret_60_z` | A_price | log(c_t/c_(t-60)) / (σ·√60) | z | klines_1m | đóng cửa nến t |
| `ret_240_z` | A_price | log(c_t/c_(t-240)) / (σ·√240) | z | klines_1m | đóng cửa nến t |
| `ret_1440_z` | A_price | log(c_t/c_(t-1440)) / (σ·√1440) | z | klines_1m | đóng cửa nến t |
| `pos_range_60` | A_price | (c−min low_60)/(max high_60−min low_60) | 0..1 | klines_1m | đóng cửa nến t |
| `pos_range_240` | A_price | (c−min low_240)/(max high_240−min low_240) | 0..1 | klines_1m | đóng cửa nến t |
| `dist_high_240_z` | F_structure | log(c/max high_240) / (σ·√240) | z | klines_1m | đóng cửa nến t |
| `dist_low_240_z` | F_structure | log(c/min low_240) / (σ·√240) | z | klines_1m | đóng cửa nến t |
| `pos_range_1440` | A_price | (c−min low_1440)/(max high_1440−min low_1440) | 0..1 | klines_1m | đóng cửa nến t |
| `dist_high_1440_z` | F_structure | log(c/max high_1440) / (σ·√1440) | z | klines_1m | đóng cửa nến t |
| `dist_low_1440_z` | F_structure | log(c/min low_1440) / (σ·√1440) | z | klines_1m | đóng cửa nến t |
| `body_15` | A_price | TB 15 nến của (c−o)/(h−l) | -1..1 | klines_1m | đóng cửa nến t |
| `uwick_15` | A_price | TB 15 nến của râu trên/(h−l) | 0..1 | klines_1m | đóng cửa nến t |
| `lwick_15` | A_price | TB 15 nến của râu dưới/(h−l) | 0..1 | klines_1m | đóng cửa nến t |
| `streak` | A_price | số nến liên tiếp cùng chiều (có dấu) | nến | klines_1m | đóng cửa nến t |
| `ema_dist_20_z` | B_trend | log(c/EMA20) / (σ·√20) | z | klines_1m | đóng cửa nến t |
| `ema_dist_60_z` | B_trend | log(c/EMA60) / (σ·√60) | z | klines_1m | đóng cửa nến t |
| `ema_dist_240_z` | B_trend | log(c/EMA240) / (σ·√240) | z | klines_1m | đóng cửa nến t |
| `ema_dist_1440_z` | B_trend | log(c/EMA1440) / (σ·√1440) | z | klines_1m | đóng cửa nến t |
| `ema_slope_60_z` | B_trend | log(EMA60_t/EMA60_(t−15)) / (σ·√15) | z | klines_1m | đóng cửa nến t |
| `ema_cross_20_60_z` | B_trend | log(EMA20/EMA60) / (σ·√60) | z | klines_1m | đóng cửa nến t |
| `adx_60` | B_trend | ADX Wilder chu kỳ 60 nến | 0..100 | klines_1m | đóng cửa nến t |
| `di_diff_60` | B_trend | +DI − −DI (60) | điểm | klines_1m | đóng cửa nến t |
| `rsi_14` | C_momentum | RSI Wilder 14 nến | 0..100 | klines_1m | đóng cửa nến t |
| `rsi_60` | C_momentum | RSI Wilder 60 nến | 0..100 | klines_1m | đóng cửa nến t |
| `macd_hist_z` | C_momentum | MACD(180,390,135) histogram / c / σ (≈MACD 12/26/9 khung 15m) | z | klines_1m | đóng cửa nến t |
| `rv_15_rel` | D_volatility | std(log return 1m, 15) / σ | tỷ lệ | klines_1m | đóng cửa nến t |
| `rv_60_rel` | D_volatility | std(log return 1m, 60) / σ | tỷ lệ | klines_1m | đóng cửa nến t |
| `rv_240_rel` | D_volatility | std(log return 1m, 240) / σ | tỷ lệ | klines_1m | đóng cửa nến t |
| `rv_ratio_60_1440` | D_volatility | std60 / std1440 (co hẹp < 1, mở rộng > 1) | tỷ lệ | klines_1m | đóng cửa nến t |
| `atr_60_rel` | D_volatility | ATR Wilder 60 / c / σ | tỷ lệ | klines_1m | đóng cửa nến t |
| `range_60_z` | D_volatility | log(max high_60 / min low_60) / (σ·√60) | z | klines_1m | đóng cửa nến t |
| `jump_15` | D_volatility | max |log return 1m| trong 15 nến / σ | z | klines_1m | đóng cửa nến t |
| `sigma_1m_bps` | D_volatility | σ_1m EWMA (halflife 1 ngày), dịch 1 nến | bps | klines_1m | đóng cửa nến t |
| `vol_ratio_30d` | D_volatility | σ / trung vị σ 30 ngày trước | tỷ lệ | klines_1m | đóng cửa nến t |
| `rvol_15` | E_volume | TB volume 15 nến / TB volume 7 ngày | tỷ lệ | klines_1m | đóng cửa nến t |
| `rvol_60` | E_volume | TB volume 60 nến / TB volume 7 ngày | tỷ lệ | klines_1m | đóng cửa nến t |
| `vol_chg_15` | E_volume | log(volume 15 nến / 15 nến trước đó) | log | klines_1m | đóng cửa nến t |
| `taker_imb_15` | E_volume | 2·taker_buy/volume − 1 trong 15 nến | -1..1 | klines_1m | đóng cửa nến t |
| `taker_imb_60` | E_volume | 2·taker_buy/volume − 1 trong 60 nến | -1..1 | klines_1m | đóng cửa nến t |
| `taker_imb_240` | E_volume | 2·taker_buy/volume − 1 trong 240 nến | -1..1 | klines_1m | đóng cửa nến t |
| `pv_corr_60` | E_volume | tương quan(log return, log(1+volume)) 60 nến | -1..1 | klines_1m | đóng cửa nến t |
| `trade_size_rel` | E_volume | TB quote/lệnh 60 nến / TB 7 ngày | tỷ lệ | klines_1m | đóng cửa nến t |
| `breakout_240` | F_structure | c > max high 240 nến TRƯỚC (không gồm nến hiện tại) | 0/1 | klines_1m | đóng cửa nến t |
| `breakdown_240` | F_structure | c < min low 240 nến trước | 0/1 | klines_1m | đóng cửa nến t |
| `false_breakout_15` | F_structure | có breakout trong 15 nến nhưng c đã quay lại dưới mức | 0/1 | klines_1m | đóng cửa nến t |
| `false_breakdown_15` | F_structure | có breakdown trong 15 nến nhưng c đã quay lại trên mức | 0/1 | klines_1m | đóng cửa nến t |
| `dc2_mode` | F_structure | hướng sóng DC thang σ×2 hiện tại (+1/−1) | dấu | klines_1m | đóng cửa nến t |
| `dc2_overshoot` | F_structure | quãng đi từ lúc xác nhận sóng / θ (thang 2) | θ | klines_1m | đóng cửa nến t |
| `dc2_pullback` | F_structure | khoảng cách tới cực trị chạy của sóng / θ (thang 2) | θ | klines_1m | đóng cửa nến t |
| `dc2_age` | F_structure | số nến từ lần xác nhận sóng gần nhất (thang 2) | nến | klines_1m | đóng cửa nến t |
| `dc4_mode` | F_structure | hướng sóng DC thang σ×4 hiện tại (+1/−1) | dấu | klines_1m | đóng cửa nến t |
| `dc4_overshoot` | F_structure | quãng đi từ lúc xác nhận sóng / θ (thang 4) | θ | klines_1m | đóng cửa nến t |
| `dc4_pullback` | F_structure | khoảng cách tới cực trị chạy của sóng / θ (thang 4) | θ | klines_1m | đóng cửa nến t |
| `dc4_age` | F_structure | số nến từ lần xác nhận sóng gần nhất (thang 4) | nến | klines_1m | đóng cửa nến t |
| `oi_chg_60` | G_futures | log(OI_t / OI_(t−60)), OI dùng từ create_time+5′ | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `oi_chg_240` | G_futures | log(OI_t / OI_(t−240)), OI dùng từ create_time+5′ | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `oi_chg_1440` | G_futures | log(OI_t / OI_(t−1440)), OI dùng từ create_time+5′ | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `oi_price_60` | G_futures | ret_60_z × sign(ΔOI 60) (H6) | z | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `ls_acct` | G_futures | log(count_long_short_ratio) gần nhất đã công bố | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `top_ls_pos` | G_futures | log(sum_toptrader_long_short_ratio) gần nhất đã công bố | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `top_ls_acct` | G_futures | log(count_toptrader_long_short_ratio) gần nhất đã công bố | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `taker_lsr_5m` | G_futures | log(sum_taker_long_short_vol_ratio) gần nhất đã công bố | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `ls_acct_chg_60` | G_futures | thay đổi log long/short tài khoản trong 60′ | log | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `metrics_staleness_min` | G_futures | số phút kể từ metrics gần nhất khả dụng | phút | metrics | create_time + 5′ ≤ đóng cửa nến t |
| `funding_last_bps` | G_futures | funding đã thanh toán gần nhất | bps | fundingRate | sau mốc thanh toán funding |
| `funding_mean3_bps` | G_futures | TB 3 lần funding gần nhất | bps | fundingRate | sau mốc thanh toán funding |
| `min_to_funding` | G_futures | số phút tới mốc funding kế tiếp (lịch 8h: 0/8/16 UTC) | phút | lịch | đóng cửa nến t |
| `hour_sin` | H_calendar | sin(2π·giờ UTC/24) | -1..1 | klines_1m | đóng cửa nến t |
| `hour_cos` | H_calendar | cos(2π·giờ UTC/24) | -1..1 | klines_1m | đóng cửa nến t |
| `dow` | H_calendar | thứ trong tuần (0 = thứ Hai) | 0..6 | klines_1m | đóng cửa nến t |
| `btc_ret_60_z` | I_cross | return 60′ của BTCUSDT / (σ symbol·√60) | z | klines BTCUSDT | đóng cửa nến t |
| `rel_ret_60_z` | I_cross | ret_60_z − btc_ret_60_z | z | klines BTCUSDT | đóng cửa nến t |
| `filler_last_60` | Z_quality | số nến filler trong 60 nến gần nhất (dùng để loại mẫu) | nến | klines_1m | đóng cửa nến t |

Đặc trưng bị loại để tránh trùng lặp: ROC (= ret_n), Stochastic %K (= pos_range_n), trend_z_1d (= ret_1440_z, tương quan 1,0).
