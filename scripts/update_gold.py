#!/usr/bin/env python3
"""抓取臺灣銀行「黃金條塊 1 公斤 本行賣出」牌價，寫入 data/gold.json。只用 Python 標準函式庫。"""
import html, json, re, ssl, sys, urllib.error, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

URL = "https://rate.bot.com.tw/gold?Lang=zh-TW"
OUT = Path(__file__).resolve().parent.parent / "data" / "gold.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9",
}
TPE = timezone(timedelta(hours=8))
PRICE = re.compile(r"\d{1,3}(?:,\d{3}){2,}|\d{7,}")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        if not isinstance(getattr(e, "reason", None), ssl.SSLError):
            raise
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return r.read().decode("utf-8", "replace")


def to_text(page):
    page = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))


def parse(page):
    text = to_text(page)
    price = None
    # 找每一個「黃金條塊」，其後不遠處要有「本行賣出」，再取之後第一個 7 位數以上的價格
    for m in re.finditer("黃金條塊", text):
        seg = text[m.end():m.end() + 500]
        j = seg.find("本行賣出")
        if j < 0 or j > 200:
            continue
        n = PRICE.search(seg[j:])
        if n:
            v = int(n.group().replace(",", ""))
            if 500_000 < v < 50_000_000:
                price = v
                break
    if price is None:
        i = text.find("本行賣出")
        print("找不到價格，網頁片段：", text[max(0, i - 200):i + 300] if i >= 0 else text[:500])
        raise ValueError("找不到「黃金條塊 本行賣出」價格")
    t = re.search(r"掛牌時間\s*[:：]\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})", text)
    return price, (t.group(1) if t else None)


def main():
    try:
        price, quoted_at = parse(fetch(URL))
    except urllib.error.HTTPError as e:
        print(f"無法取得金價：臺銀網站回應 HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("無法取得金價：", repr(e), file=sys.stderr)
        sys.exit(1)
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    if old.get("bar_1kg_sell") == price and old.get("quoted_at") == quoted_at:
        print("金價未變動，不更新。")
        return
    data = {
        "source": URL,
        "fetched_at": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"),
        "quoted_at": quoted_at,
        "bar_1kg_sell": price,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print("已更新金價：", price, quoted_at)


if __name__ == "__main__":
    main()
