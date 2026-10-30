# 幼貓濕食比價網站：更新方式

原始碼：`/workspace/cat-food-site`（box）
資料來源（唯讀，由價格追蹤 bot 每 2 天約 09:00 荷蘭時間更新）：
`/cursor/stores/store-07c67034-b23d-4a5a-9f26-e791b261bad1/cat-wetfood/prices.json`

## 結構
- `build.py`：讀 prices.json → 產生 `docs/`（index.html 內嵌資料、data.json、assets/）。不會寫入資料來源。
- `site.config.json`：商品順序、中文名稱、圖片（`target` 欄位已停用，網站不再顯示比價目標）。新商品若未設定會自動加入（使用貓咪佔位圖）。
- `web/`：版型（index.html、style.css、app.js）。
- 關注篩選：訪客可在頁首點選要看的商品，選擇存在瀏覽器 localStorage（`catfood.hidden.v1`，記錄「隱藏」的商品 id），新商品預設顯示、已移除的 id 自動忽略。
- `assets/products/`：商品圖（自行託管，不外連）。新增商品時放一張 480×480 webp 並在 config 指定。
- `shoot.py`：headless Chrome 截圖檢查（390×844、1280×800）。

## 每次更新（約每 2 天，資料更新後 10:00 以後）
```bash
cd /workspace/cat-food-site
python3 build.py                       # 重新產生 docs/
python3 shoot.py /workspace/screenshots   # 選用：截圖檢查
git add -A && git commit -m "更新價格 $(date +%F)" && git push   # GitHub Pages（main /docs）會自動部署
```

## 第一次發佈到 GitHub Pages
1. 在 GitHub 建立空的公開 repo：`yeeee0919/cat-food-prices`（不要勾 README）。
2. ```bash
   cd /workspace/cat-food-site
   gh auth login            # 或設定可推送的 remote 認證
   git remote add origin https://github.com/yeeee0919/cat-food-prices.git
   git push -u origin main
   ```
3. Repo → Settings → Pages → Source: Deploy from a branch → `main` / `/docs`。
4. 網址：https://yeeee0919.github.io/cat-food-prices/

## 備用：ShipStatic（免帳號，匿名部署 3 天後失效，需開 claim 連結保留）
```bash
npx -y @shipstatic/ship ./docs
```
