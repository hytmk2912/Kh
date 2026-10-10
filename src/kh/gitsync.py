"""Tự động đẩy báo cáo lên GitHub sau khi Colab chạy xong.

Token: GitHub fine-grained token, chỉ cấp quyền "Contents: Read and write" cho repo này, lưu trong
Colab Secrets với tên GITHUB_TOKEN. Notebook đọc token vào biến môi trường của phiên; token KHÔNG
được in ra, không ghi vào file, không ghi vào log (mọi thông báo lỗi đều bị che token).
Mỗi lần chạy đẩy lên một nhánh riêng `colab-results/<run_id>` nên không bao giờ xung đột.
Chỉ commit thư mục báo cáo (nhỏ); dữ liệu lớn nằm trên Google Drive.
"""
from __future__ import annotations

import os
import subprocess

from kh.config import REPO_ROOT, setup_logging

log = setup_logging("gitsync")
REPO_SLUG = os.environ.get("KH_GITHUB_REPO", "hytmk2912/Kh")


def _run(args: list[str], token: str | None = None, check: bool = True) -> str:
    p = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
    out = (p.stdout + p.stderr)
    if token:
        out = out.replace(token, "***")
    if check and p.returncode != 0:
        raise RuntimeError(f"git lỗi ({' '.join(a if token is None or token not in a else '***' for a in args)}): {out}")
    return out


def push_reports(P, branch: str, message: str | None = None) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Thiếu GITHUB_TOKEN (đặt trong Colab Secrets rồi chạy ô cấu hình token).")
    if not _run(["git", "config", "user.email"], check=False).strip():
        _run(["git", "config", "user.email", "kh-colab@users.noreply.github.com"])
        _run(["git", "config", "user.name", "kh-colab"])
    rel = os.path.relpath(P.reports, REPO_ROOT)
    paths = [rel]
    lock = REPO_ROOT / "configs" / "locked_strategies.yaml"
    if lock.exists():
        paths.append(os.path.relpath(lock, REPO_ROOT))
    _run(["git", "add", "-f", "--"] + paths)
    if not _run(["git", "status", "--porcelain", "--"] + paths).strip():
        log.info("Không có thay đổi để đẩy.")
        return
    _run(["git", "commit", "-q", "-m", message or f"Colab run: reports in {rel}"])
    url = f"https://x-access-token:{token}@github.com/{REPO_SLUG}.git"
    _run(["git", "push", "-q", url, f"HEAD:refs/heads/{branch}"], token=token)
    log.info("Đã đẩy %s lên nhánh %s của %s", rel, branch, REPO_SLUG)
