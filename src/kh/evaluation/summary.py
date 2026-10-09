"""Giai đoạn 9 — báo cáo tổng hợp: trạng thái mọi giả thuyết, quy luật, mô hình và chiến lược."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from kh.config import setup_logging

log = setup_logging("summary")


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def write_summary(cfg: dict, P) -> None:
    R = P.reports
    q = _load(R / "data_quality" / "quality_report.json")
    w = _load(R / "waves" / "wave_report.json")
    m = _load(R / "patterns" / "patterns_report.json")
    mo = _load(R / "models" / "models_report.json")
    bt = _load(R / "backtest" / "backtest_report.json")
    ft = _load(R / "final_test" / "final_test_report.json")
    reg = R / "experiments" / "registry.csv"
    n_exp = len(pd.read_csv(reg)) if reg.exists() else 0
    f = lambda x, d=3: "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"
    L = ["# Tổng kết nghiên cứu", "",
         "Tài liệu sinh tự động từ các báo cáo thành phần. Mọi con số là kết quả backtest/thống kê lịch sử,",
         "không phải lợi nhuận thực tế và không đảm bảo cho tương lai.", "",
         f"- Cửa sổ dữ liệu: {cfg['window']['start']} → {cfg['window']['end']} UTC; symbol: {', '.join(cfg['symbols'])}.",
         f"- Train {cfg['splits']['train'][0]} → {cfg['splits']['train'][1]}; validation {cfg['splits']['val'][0]} → {cfg['splits']['val'][1]}; "
         f"final test {cfg['splits']['test'][0]} → {cfg['splits']['test'][1]}.",
         f"- Số lần chạy thí nghiệm đã ghi trong registry: {n_exp}.", ""]
    if q:
        L += ["## 1. Dữ liệu", "", f"Tất cả tiêu chí chất lượng đạt: **{q['_gates']['all_pass']}**. "
              "Nến thiếu: 0 ở mọi coin; nến filler (bảo trì sàn) được gắn cờ và loại khỏi tín hiệu.", ""]
    L += ["## 2. Trạng thái giả thuyết đăng ký trước", "", "| ID | Nội dung | Trạng thái | Bằng chứng chính |", "|---|---|---|---|"]
    if w:
        p = w["pooled_by_scale"][f"sig{cfg['waves']['primary_scale']}"]
        tr, va = p.get("split_train", {}), p.get("split_val", {})
        ok = (tr.get("H1_p_one_sided", 1) < 0.05) and (va.get("H1_p_one_sided", 1) < 0.05)
        L.append(f"| H1 | Theo sóng DC σ×4 có lãi trước phí | {'Đạt (thống kê)' if ok else 'Không đạt'} | "
                 f"train {f(tr.get('H1_dc_follow_mean_bps'), 1)} bps (p={f(tr.get('H1_p_one_sided'))}), "
                 f"val {f(va.get('H1_dc_follow_mean_bps'), 1)} bps (p={f(va.get('H1_p_one_sided'))}); overshoot/θ ≈ {f(p['all']['overshoot_over_theta_mean'], 2)} |")
    if m:
        pre = m["preregistered"]
        desc = {"H2_breakout": "Breakout/breakdown 240′ tiếp diễn", "H3_squeeze": "Co hẹp biến động → biến động mạnh hơn",
                "H4_reversal_ret15": "Đảo chiều ngắn hạn (return 15′)", "H5_funding": "Funding cực dương → giảm",
                "H6_oi_price": "OI + giá → tiếp diễn", "H7_taker_imb": "Mất cân bằng taker dự báo return"}
        for k, d in desc.items():
            r = pre[k]
            if "ic_train" in r:
                ev = f"IC train {f(r['ic_train'], 4)} (t={f(r['t_train'], 1)}), val {f(r['ic_val'], 4)} (t={f(r['t_val'], 1)})"
            elif k == "H2_breakout":
                ev = f"Δ tỷ lệ lên sau breakout: train {f(r['train']['breakout_up_rate']['diff'], 4)}, val {f(r['val']['breakout_up_rate']['diff'], 4)}"
            else:
                ev = f"Δ biên độ/rào: train {f(r['train']['diff'], 3)}, val {f(r['val']['diff'], 3)} (ngược giả thuyết nếu âm)"
            st = "Đạt (thống kê), chưa đủ để giao dịch" if r.get("pass") else "Không đạt"
            L.append(f"| {k.split('_')[0]} | {d} | {st} | {ev} |")
    if mo:
        for H, v in mo["by_H"].items():
            h8 = v["H8"]
            L.append(f"| H8 (H={H}) | LightGBM có skill > 0 walk-forward | {'Đạt (thống kê)' if h8['pass'] else 'Không đạt'} | "
                     f"skill TB {f(h8['mean_fold_skill'], 5)}, t={f(h8['t'], 2)}, coin > 0: {h8['coins_positive']}/5 |")
    if m:
        s = m["summary"]
        L += ["", "## 3. Quét exploratory", "",
              f"- {s['n_univariate_tests']} kiểm định đơn biến + {s['n_pair_tests']} tổ hợp; qua FDR train (ALL): {s['univariate_fdr_train_ALL']}; "
              f"qua cả validation và ≥ 3/5 coin: {s['univariate_full_pass_ALL']}; tổ hợp qua FDR + validation: {s['pairs_fdr_and_val']}.",
              f"- Ngưỡng xác suất thắng hòa vốn: " + ", ".join(f"H={h}: {f(p)}" for h, p in s["breakeven_prob"].items()) + ".",
              "- Không quy luật đơn biến nào có decile cực trị vượt ngưỡng hòa vốn trên validation "
              if not any(c["status"].startswith("Có tiềm năng") for c in m["candidates"].values())
              else "- Có quy luật vượt ngưỡng hòa vốn ở decile cực trị — xem báo cáo chi tiết.", ""]
    if bt:
        L += ["## 4. Chiến lược trên validation (sau chi phí)", "", "| Biến thể | Lệnh | Ròng USD | Sharpe | PF | Exp ròng bps | Exp gộp bps | DSR | Chọn |",
              "|---|---|---|---|---|---|---|---|---|"]
        for n, r in bt["variants"].items():
            b = r["base"]
            L.append(f"| {n} | {b['n_trades']} | {f(b.get('net_pnl'), 0)} | {f(b.get('sharpe'), 2)} | {f(b.get('profit_factor'), 2)} | "
                     f"{f(b.get('expectancy_bps'), 1)} | {f(b.get('gross_expectancy_bps'), 1)} | {f(r['dsr']['dsr'])} | {r['criteria']['selected']} |")
        L += ["", f"PBO = {f(bt['pbo'].get('pbo'))}. Được chọn vào final test: **{', '.join(bt['selected']) or 'không có'}**.", ""]
    if ft:
        L += ["## 5. Final test", "", f"Chế độ {ft['mode']}, chạy {ft['run_at_utc']}, khóa {ft['lock_hash']}.", "",
              "| Biến thể | Trạng thái | Lệnh | Ròng USD | Sharpe | PF | Exp ròng bps |", "|---|---|---|---|---|---|---|"]
        for n, r in ft["results"].items():
            b = r["base"]
            L.append(f"| {n} | {r['status']} | {b['n_trades']} | {f(b.get('net_pnl'), 0)} | {f(b.get('sharpe'), 2)} | "
                     f"{f(b.get('profit_factor'), 2)} | {f(b.get('expectancy_bps'), 1)} |")
        L.append(f"\nMua & giữ trên test: {ft['buy_hold']['total_return'] * 100:.2f}%.")
    else:
        L += ["## 5. Final test", "", "Chưa chạy.", ""]
    L += ["", "## 6. Giới hạn chính", "",
          "- 2 năm dữ liệu, 5 coin vốn hóa lớn tương quan cao; final test 146 ngày có thể chỉ chứa một vài chế độ thị trường.",
          "- Không có dữ liệu spread lịch sử; slippage là giả định (2 bps/chiều, kiểm tra thêm ×3).",
          "- Phí giả định VIP0 taker 0,05%; tài khoản thật có thể khác.",
          "- Thứ tự giá trong nến 1 phút không biết → TP/SL cùng nến tính là SL (thận trọng).",
          "- Không mô phỏng sổ lệnh, độ trễ mạng, thanh lý theo mark price; đường vốn tính theo lệnh đã đóng.",
          "- Funding tháng 10/2026 chưa được Binance công bố tại thời điểm chạy → ước tính bằng mức cuối cùng.",
          "- Một lỗi phương pháp (IC trong ngày) đã được phát hiện và sửa; xem nhật ký thay đổi trong docs/hypotheses.md."]
    (R / "SUMMARY.md").write_text("\n".join(L) + "\n")
    log.info("Đã ghi %s", R / "SUMMARY.md")
