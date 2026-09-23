#!/usr/bin/env python3
"""抓取臺灣銀行「黃金條塊 1 公斤 本行賣出」牌價，寫入 data/gold.json。只用 Python 標準函式庫。"""
import html, json, re, ssl, sys, urllib.error, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

URL = "https://rate.bot.com.tw/gold?Lang=zh-TW"
OUT = Path(__file__).resolve().parent.parent / "data" / "gold.json"
UA = "Mozilla/5.0 (rate-table updater; GitHub Actions)"
TPE = timezone(timedelta(hours=8))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def to_text(page):
    page = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))


def parse(page):
    text = to_text(page)
    # 表格列：黃金條塊 | 本行賣出 | 1 公斤 | 500 公克 | 250 公克 | 100 公克
    m = re.search(r"黃金條塊\s*本行賣出\s*([\d,]{7,})", text)
    if not m:
        raise ValueError("找不到「黃金條塊 本行賣出」欄位，臺銀網頁格式可能已變更")
    price = int(m.group(1).replace(",", ""))
    if not 500_000 < price < 50_000_000:
        raise ValueError(f"金價數值異常：{price}")
    t = re.search(r"掛牌時間\s*[:：]\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})", text)
    return price, (t.group(1) if t else None)


def main():
    try:
        price, quoted_at = parse(fetch(URL))
    except Exception as e:  # noqa: BLE001
        print("無法取得金價：", e, file=sys.stderr)
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
