from flask import Flask, render_template, request, redirect
import pandas as pd
from datetime import datetime, timedelta
import requests
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

WEATHER_API_KEY = os.getenv("VISUAL_API_KEY") or "R7QNF6MDDL3YE8D5SY3A3XGQH"

def get_weather(date, city="Seoul"):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{date}/{date}?unitGroup=metric&include=days&key={WEATHER_API_KEY}&contentType=json"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    try:
        data = res.json()["days"][0]
        return {
            "temp": data.get("temp", 0),
            "humidity": data.get("humidity", 0),
            "windspeed": data.get("windspeed", 0),
            "precip": data.get("precip", 0)
        }
    except:
        return None

def is_workable(process, temp, humidity, windspeed, precip):
    if precip > 2:
        return False, "강수량"
    if temp < -5 or temp > 35:
        return False, "온도"
    if humidity > 90 and "도장" in process:
        return False, "습도"
    if "타설" in process and precip > 0:
        return False, "비 예보"
    return True, "가능"

@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["csv_file"]
        if file and file.filename.endswith(".csv"):
            path = os.path.join(UPLOAD_FOLDER, "latest.csv")
            file.save(path)
            return redirect("/result")
    return render_template("upload.html")

@app.route("/result")
def result():
    path = os.path.join(UPLOAD_FOLDER, "latest.csv")
    if not os.path.exists(path):
        return "No file uploaded yet.", 400
    df = pd.read_csv(path)
    results = []
    for _, row in df.iterrows():
        process = row["공정명"]
        start = pd.to_datetime(row["시작일"])
        end = pd.to_datetime(row["종료일"])
        total_days = (end - start).days + 1
        ok_days = 0
        reasons = []
        for i in range(total_days):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            weather = get_weather(date)
            if weather:
                workable, reason = is_workable(process, **weather)
                if workable:
                    ok_days += 1
                else:
                    reasons.append(f"{date}: {reason}")
        extension = max(0, total_days - ok_days)
        results.append({
            "공정명": process,
            "기간": f"{start.date()} ~ {end.date()}",
            "총일수": total_days,
            "작업가능일수": ok_days,
            "예상연장": extension,
            "불가사유": "; ".join(reasons)
        })
    return render_template("result.html", results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)