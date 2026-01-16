from selenium import webdriver
from selenium.webdriver.common.by import By
from flask import Flask
import json
from flask import Response
import time
from bs4 import BeautifulSoup
import copy
import datetime
import re
from datetime import datetime, timezone, timedelta
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os

timetable_true = {"月":["英語講読Ⅰ(3E)","電気回路Ⅰ(3E)","総合数学(3E)","特別講義(3E)"],
                  "火":["解析学Ⅱ(3E)","電気機器Ⅰ(3E)","プログラミングⅡ(3E)","電気磁気学Ⅰ(3E)"],
                  "水":["電子回路Ⅰ(3E)","総合英語(3E)","保健体育Ⅲ(3E)","特活(3E)"],
                  "木":["政治・経済(3E)","総合物理(3E)","電気電子工学実験Ⅰ(3E)","電気電子工学実験Ⅰ(3E)"],
                  "金":["応用物理Ⅰ(3E)","解析学Ⅱ(3E)","国語Ⅲ(3E)","特別講義(3E)"],}

# -----------------------------
# 1. Chrome を起動 このPCで
# -----------------------------
#driver = webdriver.Chrome()

# -----------------------------
# 1. Chrome を VPS 用に起動
# -----------------------------
options = Options()
options.add_argument("--headless=new")  # 新しいヘッドレスモード
options.add_argument("--no-sandbox")  # root 実行時に必須
options.add_argument("--disable-dev-shm-usage")  # VPS では必須
options.add_argument("--disable-gpu") #GPU無効化
options.add_argument("--disable-software-rasterizer")# ソフトウェアによる描画処理を無効化。GPU がない環境での描画エラーを防ぐ。
options.add_argument("--window-size=1920,1080") #- 仮想ブラウザの画面サイズを指定。

driver = webdriver.Chrome(options=options)#設定したオプションをChromeに渡す


# -----------------------------
# 2. ログインページへアクセス
# -----------------------------
driver.get("https://std.ishikawa-nct.ac.jp/login")
time.sleep(1)

# -----------------------------
# 3. ログイン処理
# -----------------------------
load_dotenv()  # .env を読み込む

LOGIN_ID = os.getenv("LOGIN_ID")
PASSWORD = os.getenv("PASSWORD")

driver.find_element(By.ID, "login-user").send_keys(LOGIN_ID)
driver.find_element(By.ID, "login-password").send_keys(PASSWORD)
driver.find_element(By.NAME, "act").click()

time.sleep(2)

# -----------------------------
# 4. 時間割ページへ移動
# -----------------------------
TIMETABLE_URL = "https://std.ishikawa-nct.ac.jp/"  # 必要に応じて変更
driver.get(TIMETABLE_URL)
time.sleep(2)

# -----------------------------
# 5. HTML を取得して BeautifulSoup で解析
# -----------------------------
soup = BeautifulSoup(driver.page_source, "html.parser")

# 時間割の <tr> を取得（class="text-center"）
rows = soup.find_all("tr", class_="text-center")

timetable = {}
current_date = None
buffer = []

for row in rows:
    tds = row.find_all("td")

    # 日付セル（rowspan がある）
    if tds and "rowspan" in tds[0].attrs:
        # 前の日付のデータを保存
        if current_date and buffer:
            timetable[current_date] = buffer
            buffer = []

        current_date = tds[0].get_text(strip=True)
        tds = tds[1:]  # 日付セルを除く

    # 授業番号行（1,2,3,4 / 5,6,7,8）
    texts = [td.get_text(strip=True) for td in tds]

    # 空欄を除いて、すべて数字なら番号行としてスキップ
    if all(t.isdigit() for t in texts if t != ""):
        continue

    # 授業名行
    subjects = [td.get_text(strip=True) for td in tds]
    buffer.extend(subjects)

# 最後の日付も保存
if current_date and buffer:
    timetable[current_date] = buffer

driver.quit()

for date in timetable:
    timetable[date] = timetable[date][::2]

# -----------------------------
# 6. 結果を表示
# -----------------------------
for date, subjects in timetable.items():
    print(f"=== {date} ===")
    for i, sub in enumerate(subjects, start=1):
        print(f"{i}コマ目: {sub}")
    print()


#timetable編集

timetable2 = copy.deepcopy(timetable)

today = list(timetable2.keys())[0]

today_timetable = timetable2.pop(today)

print(f'今日の時間割:{today_timetable}')
print()

#---------------------------------------------------------------------------------------------------------

def get_weekday_from_tail(date_str):
    # 例: "12月29日(月)" → "月"
    if len(date_str) < 2:
        return None
    return date_str[-2]  # 後ろから2番目

def normalize(s):
    if not s:
        return s

    # 全角カッコを半角に
    s = s.replace("（", "(").replace("）", ")")

    # ローマ数字を統一
    s = s.replace("Ⅰ", "I").replace("Ⅱ", "II").replace("Ⅲ", "III")

    # 全角スペース削除
    s = s.replace("　", "")

    # 余分なスペース削除
    s = re.sub(r"\s+", "", s)

    return s

# 日本時間（UTC+9）
JST = timezone(timedelta(hours=9))

now = datetime.now(JST)
formatted = now.isoformat(timespec="seconds")

diff = {}
TimeTables = {"genereted_at":formatted}
main_timetable = []

for date, subjects in timetable.items():
    weekday = get_weekday_from_tail(date)

    # 土日スキップ
    if weekday in ["土", "日"]:
        continue

    if subjects == ["休講日"]:
        continue

    expected = list(timetable_true.get(weekday, []))

    subjects_norm = [normalize(x) for x in subjects]
    expected_norm = [normalize(x) for x in expected]

    # 完全一致チェック
    if subjects_norm != expected_norm:
        diff[date] = {
            "actual": subjects_norm,
            "expected": expected_norm,
        }

        subjects_norm = [s[:-4] for s in subjects_norm] #(3E)を消す

        subjects = []
        TimeTable = {}

        for period, subject in zip(range(4),subjects_norm):
            Subject = {}
            Subject["period"] = period+1
            Subject["subject"] = subject
            subjects.append(Subject)

        TimeTable["subjects"] = subjects
        TimeTable["date"] = date
        main_timetable.append(TimeTable)
    
    TimeTables["main_timetable"] = main_timetable

# 結果表示
for date, info in diff.items():
    print(f"=== {date} ===")
    print("実際:", info["actual"])
    print("正しい:", info["expected"])
    print()

#------------------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/timetable", methods=["GET"])

def handle_get():
    return Response(
    json.dumps(TimeTables, ensure_ascii=False, sort_keys=False),
    mimetype='application/json'
)


if __name__ == "__main__":
    # 0.0.0.0 にすると外部（VPS）からアクセス可能
    app.run(host="0.0.0.0", port=8080)
