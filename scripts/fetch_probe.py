#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_probe.py — 批量探测 URL 可用性，识别拦截类型，给出降级路径建议

对应 S1 取证链。用法：

    # 探测多个 URL（联网）
    python fetch_probe.py https://a.com/x https://b.com/y

    # 从文件读取（一行一个 URL，# 开头为注释）
    python fetch_probe.py --file urls.txt

    # 离线分类已保存的 HTML（不联网，用于回归测试或事后分析）
    python fetch_probe.py --html-dir ./saved_pages

输出：终端表格 + probe_report.json

设计原则
--------
* **只探测，不绕过。** 检测到验证码/付费墙时如实报告并给替代路径，
  不尝试验证码破解、不填 Cookie、不使用代理池。
* **离线模式可复现。** 分类逻辑与网络无关，便于回归测试。
* **不解析正文内容。** 只判断"能不能用"，内容分析交给上层流程。

分类枚举
--------
ok         可用
captcha    人机验证
forbidden  403
ratelimit  429 / 速率限制
timeout    超时
conn_error 连接失败 / DNS 失败
js_shell   JS 空壳（HTML 巨大但几乎无可见文本）
paywall    付费墙
login      登录墙
soft404    200 但内容为"页面不存在"
robots     明确禁止抓取 / 无访问权限
too_large  内容过大（可能触发截断，需换更精确 URL）
error      其他异常
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import zlib
from typing import Dict, List, Optional
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

# 分类判定顺序：从强特征到弱特征。越靠前越确定。
MARKERS = [
    # (分类, [特征串], 说明)
    ("captcha", ["recaptcha", "g-recaptcha", "captcha-form", "unusual traffic",
                 "please enable javascript and cookies", "are you a robot",
                 "verify you are human", "unusual traffic from your computer network"],
     "人机验证"),
    ("robots", ["access denied", "your ip has been blocked", "request blocked",
                "you do not have permission", "forbidden by robots"],
     "明确禁止访问"),
    ("login", ["please log in", "please sign in", "log in to continue",
               "sign in to continue", "create an account to continue",
               "this content is only available to"],
     "登录墙"),
    ("paywall", ["purchase this article", "buy this article", "institutional access",
                 "subscribe to read", "rent this article", "get access to the full",
                 "members-only", "paywall"],
     "付费墙"),
    ("soft404", ["page not found", "404 not found", "this page does not exist",
                 "page you are looking for", "content is no longer available",
                 "we can't find the page"],
     "软 404"),
]

# JS 空壳判定阈值
SHELL_HTML_MIN = 20000      # HTML 字节数下限
SHELL_TEXT_MAX = 500        # 可见文本字符数上限

BLOCK_HINTS = {
    "captcha": "改用同主体其他站点（机构页/个人站），或结构化档案（ORCID/arXiv/SSRN）",
    "forbidden": "换路径；降低请求频率；不要重试轰炸",
    "ratelimit": "退避后重试一次，或换路径；降低并发",
    "timeout": "换路径；该站点可能对非浏览器客户端不友好",
    "conn_error": "检查 URL 拼写与网络；可能需要浏览器环境",
    "js_shell": "找静态镜像/打印版，或改用 API（arXiv API、Semantic Scholar API）",
    "paywall": "只取可见摘要；换开放获取来源（arXiv/SSRN/作者主页）",
    "login": "换路径；公开档案通常无需登录",
    "soft404": "URL 失效，回到来源清单找替代路径",
    "robots": "遵守站点意愿，换路径",
    "too_large": "换更精确的 URL（列表页而非首页），分 section 抓取",
}

# 已知的"传输成功但内容由 JS 渲染"站点：raw HTML 里常常没有目标内容。
# 这类站点即使判定为 ok，也必须人工确认目标内容是否真的在响应里。
JS_RENDERED_HINTS = {
    "scholar.google.com": "论文列表由 JS 渲染，raw HTML 常只有框架；改用 Semantic Scholar / ORCID API 取结构化数据",
    "www.linkedin.com": "内容高度个性化且 JS 渲染，raw HTML 通常不含履历正文",
    "x.com": "内容由 JS 加载，且需登录才可见完整内容",
    "twitter.com": "同上",
    "www.facebook.com": "同上",
}


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def visible_text_len(html: str) -> int:
    """粗略估计可见文本长度：去掉 script/style/注释后再统计。"""
    s = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"&[a-z#0-9]+;", " ", s)
    return len(re.sub(r"\s+", " ", s).strip())


def classify(html: str, status: Optional[int] = None,
             content_type: Optional[str] = None) -> Dict[str, object]:
    """核心分类函数：与网络无关，可离线测试。"""
    low = html.lower()
    n_bytes = len(html)
    n_text = visible_text_len(html)

    if status is not None and status in (401, 403):
        return {"status": "forbidden", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": f"HTTP {status}"}
    if status is not None and status == 429:
        return {"status": "ratelimit", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": "HTTP 429"}
    if status is not None and status >= 400:
        return {"status": "error", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": f"HTTP {status}"}

    for kind, needles, detail in MARKERS:
        for nd in needles:
            if nd in low:
                return {"status": kind, "http": status, "bytes": n_bytes, "text": n_text,
                        "detail": detail + f"（命中 “{nd}”）"}

    if n_bytes >= SHELL_HTML_MIN and n_text < SHELL_TEXT_MAX:
        return {"status": "js_shell", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": f"HTML {n_bytes}B 但可见文本仅 {n_text} 字符，疑似 JS 渲染"}

    if n_text == 0:
        return {"status": "js_shell", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": "无可见文本"}
    if n_bytes > 3_000_000:
        return {"status": "too_large", "http": status, "bytes": n_bytes, "text": n_text,
                "detail": f"{n_bytes/1e6:.1f}MB，可能触发截断"}

    return {"status": "ok", "http": status, "bytes": n_bytes, "text": n_text,
            "detail": f"可见文本 {n_text} 字符"}


def fetch(url: str, timeout: float = 20.0, max_bytes: int = 3_000_000) -> Dict[str, object]:
    """抓取单个 URL 并分类。不绕过任何拦截。"""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }
    req = urlrequest.Request(url, headers=headers, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(max_bytes + 1)
            enc = (resp.headers.get("Content-Encoding") or "").lower()
            ctype = resp.headers.get("Content-Type")
            status = getattr(resp, "status", None) or resp.getcode()
    except HTTPError as e:
        try:
            raw = e.read(max_bytes)
        except Exception:
            raw = b""
        enc, ctype, status = "", None, e.code
    except URLError as e:
        reason = getattr(e, "reason", e)
        kind = "timeout" if "timed out" in str(reason).lower() else "conn_error"
        return {"url": url, "status": kind, "http": None, "bytes": 0, "text": 0,
                "detail": str(reason)[:120], "hint": BLOCK_HINTS.get(kind, "")}
    except Exception as e:  # noqa: BLE001 — 探测脚本应永不因异常中断
        return {"url": url, "status": "error", "http": None, "bytes": 0, "text": 0,
                "detail": f"{type(e).__name__}: {e}"[:120], "hint": "换路径"}

    if enc == "gzip":
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    elif enc == "deflate":
        try:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        except Exception:
            pass

    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    html = raw.decode("utf-8", errors="replace")

    res = classify(html, status=status, content_type=ctype)
    res["url"] = url
    res["host"] = urlparse(url).netloc
    if truncated:
        res["status"] = "too_large"
        res["detail"] = f"内容超过 {max_bytes}B，已截断"
    res.setdefault("hint", BLOCK_HINTS.get(res["status"], ""))

    # 传输成功 ≠ 内容可用：已知 JS 渲染站点即使 200 也可能不含目标内容
    host = urlparse(url).netloc.lower().replace("www.", "")
    if res["status"] == "ok":
        for known, note in JS_RENDERED_HINTS.items():
            if host.endswith(known):
                res["content_note"] = note
                res["detail"] += "；⚠ " + note
                break
    return res


def probe_html_file(path: str) -> Dict[str, object]:
    """离线分类一个已保存的 HTML 文件。"""
    with open(path, "rb") as f:
        raw = f.read(3_000_001)
    truncated = len(raw) > 3_000_000
    html = raw.decode("utf-8", errors="replace")
    res = classify(html)
    res["url"] = path
    res["host"] = os.path.basename(path)
    res["truncated_on_disk"] = truncated
    res.setdefault("hint", BLOCK_HINTS.get(res["status"], ""))
    return res


def report(results: List[Dict[str, object]]) -> str:
    ok = [r for r in results if r["status"] == "ok"]
    bad = [r for r in results if r["status"] != "ok"]
    L = []
    A = L.append
    A("=" * 78)
    A(f"{'URL / 文件':<44} {'判定':<12} {'字节':>10} {'可见文本':>8}")
    A("-" * 78)
    for r in results:
        url = str(r.get("url", ""))
        short = url if len(url) <= 43 else url[:40] + "..."
        A(f"{short:<44} {str(r['status']):<12} {int(r.get('bytes', 0)):>10,} {int(r.get('text', 0)):>8,}")
        if r.get("detail"):
            A(f"    └─ {r['detail']}")
        if r.get("content_note"):
            A(f"    ⚠ 内容完整性存疑: 需人工确认目标内容确实在响应中")
        if r.get("hint"):
            A(f"    → 降级建议: {r['hint']}")
    A("=" * 78)
    A(f"可用 {len(ok)} / 共 {len(results)}")
    if ok and bad:
        A("\n下一步：对可用来源跑来源台账分级；对被拦截来源建立降级路径，不要用推测填补。")
    elif bad and not ok:
        A("\n下一步：全部被拦截。按降级顺序换路径，或向用户索取本地材料。")
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    _configure_stdio()
    ap = argparse.ArgumentParser(description="批量探测 URL 可用性并识别拦截类型")
    ap.add_argument("urls", nargs="*", help="要探测的 URL")
    ap.add_argument("--file", help="从文件读取 URL（一行一个，# 为注释）")
    ap.add_argument("--html-dir", help="离线分类目录下已保存的 HTML（不联网）")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--max-bytes", type=int, default=3_000_000)
    ap.add_argument("--out", default="probe_report.json")
    args = ap.parse_args(argv)

    results: List[Dict[str, object]] = []

    if args.html_dir:
        if not os.path.isdir(args.html_dir):
            print(f"[错误] 目录不存在: {args.html_dir}", file=sys.stderr)
            return 2
        for name in sorted(os.listdir(args.html_dir)):
            p = os.path.join(args.html_dir, name)
            if os.path.isfile(p) and name.lower().endswith((".html", ".htm", ".txt")):
                results.append(probe_html_file(p))
    else:
        urls = list(args.urls)
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
        if not urls:
            ap.print_help()
            return 2
        for u in urls:
            results.append(fetch(u, timeout=args.timeout, max_bytes=args.max_bytes))

    print(report(results))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[完成] 详细结果已写入 {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
