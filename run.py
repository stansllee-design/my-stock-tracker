import json
import requests

print("開始抓取台灣證交所資料...")

# 1. 抓取當日收盤行情與漲跌幅
price_url = (
    "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=json"
)
price_res = requests.get(
    price_url, headers={"User-Agent": "Mozilla/5.0"}
).json()

stock_dict = {}
for row in price_res.get("data", []):
    try:
        code = row[0].strip()
        name = row[1].strip()
        close = float(row[7].replace(",", ""))
        change_pct = float(row[9].replace(",", ""))
        stock_dict[code] = {
            "code": code,
            "name": name,
            "close": close,
            "change_pct": change_pct,
            "inst_net": 0,
        }
    except Exception:
        continue

# 2. 抓取三大法人買賣超 (T86)
t86_url = (
    "https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL"
)
t86_res = requests.get(t86_url, headers={"User-Agent": "Mozilla/5.0"}).json()

for row in t86_res.get("data", []):
    try:
        code = row[0].strip()
        total_net = int(row[18].replace(",", ""))  # 法人合計買賣超股數
        if code in stock_dict:
            # 估算買賣金額 (百萬元) = 股數 * 收盤價 / 1,000,000
            stock_dict[code]["inst_net"] = round(
                (total_net * stock_dict[code]["close"]) / 1_000_000, 2
            )
    except Exception:
        continue

stocks = list(stock_dict.values())

# 3. 計算多空分數：漲跌幅占 60% + 法人買賣金額占 40%
for s in stocks:
    # 避免極端值干擾，限制金額評分範圍
    inst_score = max(-50, min(50, s["inst_net"] * 0.2))
    s["score"] = round(s["change_pct"] * 6 + inst_score, 1)

# 4. 排序抓出多方前 20 與 空方前 20
bull_20 = sorted(stocks, key=lambda x: x["score"], reverse=True)[:20]
bear_20 = sorted(stocks, key=lambda x: x["score"])[:20]

# 5. 輸出存檔成 data.json
result = {"bull_top20": bull_20, "bear_top20": bear_20}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("完成！已產出今日多空前20大股票。")
