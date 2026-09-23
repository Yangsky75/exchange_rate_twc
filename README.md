# 每旬匯率換算表

旅客攜帶外幣、黃金入境申報試算網頁。資料由 GitHub Actions 自動更新：

| 資料 | 來源 | 更新時間（臺灣時間） |
| --- | --- | --- |
| 每旬報關適用外幣匯率 | 關港貿單一窗口 GC331「目前匯率 TXT」 | 每月 1、2、11、12、21、22 日 08:30 |
| 黃金條塊 1 公斤本行賣出 | 臺灣銀行黃金牌價 | 週一至週五 09:40、15:40 |

資料沒有變動時不會產生 commit。

## 部署步驟

1. 在 GitHub 建立新的 repository，把這個資料夾的所有檔案（包含隱藏的 `.github` 資料夾）上傳。
2. **Settings → Pages**：Source 選 `Deploy from a branch`，Branch 選 `main`、資料夾 `/ (root)`。
3. **Settings → Actions → General → Workflow permissions**：選 `Read and write permissions` 後儲存。
4. **Actions** 分頁：分別對「更新海關每旬匯率」「更新臺銀黃金牌價」按 `Run workflow` 手動跑一次，確認成功（綠勾）。
5. 開啟 `https://<帳號>.github.io/<repo 名稱>/` 即可使用；也可以嵌入 Google 協作平台。

## 檔案

- `index.html`：網頁本體，讀取 `data/*.json`；讀不到時使用內建資料。
- `data/rates.json`、`data/gold.json`：自動更新的資料（目前匯率為範例資料，第一次執行後覆蓋）。
- `scripts/update_rates.py`、`scripts/update_gold.py`：抓取程式，只用 Python 標準函式庫。
- `.github/workflows/`：排程設定。

## 自動更新失敗時

- 到 Actions 分頁看錯誤訊息。若關港貿網站拒絕 GitHub 的海外連線，可改在自己的電腦用工作排程器執行 `python scripts/update_rates.py` 後 push，或直接用網頁下方「手動更新資料」匯入 TXT 檔。
- 公開 repo 若連續 60 天沒有任何 commit，GitHub 會暫停排程；金價每個工作日都會 commit，一般不會發生。
