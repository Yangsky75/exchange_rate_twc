#!/usr/bin/env python3
"""下載關港貿單一窗口 (GC331) 每旬報關適用外幣匯率，寫入 data/rates.json。
只有匯率內容有變動時才改寫檔案，避免產生無意義的 commit。只用 Python 標準函式庫。"""
import json, re, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

URLS = [
    "https://portal.sw.nat.gov.tw/APGQ/GC331!downLoad?formBean.downLoadFile=CURRENT_TXT",
    "http://portal.sw.nat.gov.tw/APGQ/GC331!downLoad?formBean.downLoadFile=CURRENT_TXT",
]
OUT = Path(__file__).resolve().parent.parent / "data" / "rates.json"
UA = "Mozilla/5.0 (rate-table updater; GitHub Actions)"
TPE = timezone(timedelta(hours=8))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except (ssl.SSLError, urllib.error.URLError) as e:
        if not isinstance(getattr(e, "reason", e), ssl.SSLError):
            raise
        # 部分政府網站憑證鏈不完整，改用不驗證憑證的連線重試一次
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return r.read()


def decode(raw):
    for enc in ("utf-8-sig", "cp950", "big5hkscs"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


# 空白/逗號分隔：USD 115 09 3 30.215 30.315
LINE_WS = re.compile(r"^([A-Z]{3})[\s,]+(\d{2,3})[\s,]+(\d{1,2})[\s,]+([123])[\s,]+([\d.]+)(?:[\s,]+([\d.]+))?")
# 固定欄寬：USD1150931 30.215 30.315
LINE_FW = re.compile(r"^([A-Z]{3})(\d{3})(\d{2})([123])\s*([\d.]+)(?:\s+([\d.]+))?")


def parse(text):
    rates, period = {}, None
    for line in text.splitlines():
        line = line.strip()
        m = LINE_WS.match(line) or LINE_FW.match(line)
        if not m:
            continue
        code, y, mo, p, buy, sell = m.groups()
        try:
            buy = float(buy)
        except ValueError:
            continue
        sell = float(sell) if sell else None
        rates[code] = {"buy": buy, "sell": sell}
        period = period or {"year": int(y), "month": int(mo), "period": int(p)}
    return period, rates


def main():
    last_err = None
    for url in URLS:
        try:
            period, rates = parse(decode(fetch(url)))
            if "USD" in rates and len(rates) >= 15:
                break
            last_err = f"解析結果不完整（只有 {len(rates)} 種幣別）"
        except Exception as e:  # noqa: BLE001
            last_err = repr(e)
    else:
        print("無法取得匯率：", last_err, file=sys.stderr)
        sys.exit(1)

    rates.setdefault("TWD", {"buy": 1, "sell": 1})
    rates = dict(sorted(rates.items()))
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    if old.get("period") == period and old.get("rates") == rates:
        print("匯率未變動，不更新。", period)
        return
    data = {
        "source": URLS[0],
        "fetched_at": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"),
        "period": period,
        "rates": rates,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print("已更新匯率：", period, len(rates), "種幣別")


if __name__ == "__main__":
    main()
