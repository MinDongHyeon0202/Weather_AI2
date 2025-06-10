
from flask import Flask, render_template, request
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

model = joblib.load("ai_model.pkl")
le_job = joblib.load("job_encoder.pkl")
le_result = joblib.load("result_encoder.pkl")

JOB_OPTIONS = {
    "formwork": "외부비계설치",
    "concrete_floor": "기초타설",
    "interior_paint": "내부 도장",
    "floor_finish": "방통",
    "floor1": "1층 타설",
    "roof": "지붕 타설"
}

def predict_with_ai(job, temp, humidity, wind, rain):
    try:
        job_code = le_job.transform([job])[0]
        features = np.array([[temp, humidity, wind, rain, job_code]])
        pred = model.predict(features)
        return le_result.inverse_transform(pred)[0]
    except Exception as e:
        return f"에러: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    today = datetime.now(pytz.timezone("Asia/Seoul")).date()
    result_list = []
    selected_job = request.form.get("job_type", "concrete_floor")
    start = request.form.get("start_date", str(today))
    end = request.form.get("end_date", str(today + timedelta(days=7)))

    if request.method == "POST":
        for i in range(7):
            date = datetime.strptime(start, "%Y-%m-%d") + timedelta(days=i)
            temp = 20 + i
            humidity = 60 + (i % 3) * 10
            wind = 1.5
            rain = 0.0 if i % 2 == 0 else 3.0

            prediction = predict_with_ai(selected_job, temp, humidity, wind, rain)
            result_list.append({
                "날짜": date.strftime("%Y-%m-%d"),
                "온도": temp,
                "습도": humidity,
                "풍속": wind,
                "강수량": rain,
                "예측결과": prediction
            })

    return render_template("index.html",
        results=result_list,
        job_options=JOB_OPTIONS,
        job_key=selected_job,
        start_date=start,
        end_date=end
    )

if __name__ == "__main__":
    app.run(debug=True)
