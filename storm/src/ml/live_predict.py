import os
import requests
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler

# Reduce TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# =======================
# CONFIGURATION
# =======================

SEQ_LENGTH = 24
PRED_HORIZON = 24

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lstm_all_andrew_clean.h5")

WEB_DIR = os.path.join(os.path.dirname(BASE_DIR), "Web", "forecast")
OUT_CSV = os.path.join(WEB_DIR, "output_pred.csv")
HISTORY_CSV = os.path.join(WEB_DIR, "history.csv")

# NOAA rolling datasets (stable endpoints)
PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json"
MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json"

# =======================
# SAFE JSON PARSER
# =======================

def safe_parse_json(response):
    text = response.text.strip()
    first = text.find('[')
    last = text.rfind(']')
    if first == -1 or last == -1:
        raise ValueError("No valid JSON array found")
    cleaned = text[first:last+1]
    return json.loads(cleaned)

# =======================
# BUILD 72H TIME SERIES
# =======================

def build_time_series():

    plasma_response = requests.get(PLASMA_URL, timeout=15)
    plasma_response.raise_for_status()

    mag_response = requests.get(MAG_URL, timeout=15)
    mag_response.raise_for_status()

    plasma_json = safe_parse_json(plasma_response)
    mag_json = safe_parse_json(mag_response)

    plasma_df = pd.DataFrame(plasma_json[1:], columns=plasma_json[0])
    mag_df = pd.DataFrame(mag_json[1:], columns=mag_json[0])

    plasma_df["time_tag"] = pd.to_datetime(plasma_df["time_tag"])
    mag_df["time_tag"] = pd.to_datetime(mag_df["time_tag"])

    plasma_df.set_index("time_tag", inplace=True)
    mag_df.set_index("time_tag", inplace=True)

    plasma_df = plasma_df.apply(pd.to_numeric, errors="coerce")
    mag_df = mag_df.apply(pd.to_numeric, errors="coerce")

    df = pd.merge(
        plasma_df,
        mag_df,
        left_index=True,
        right_index=True,
        how="inner"
    )
    

    df = df.sort_index()

    # Keep last 72 hours
    end_time = df.index.max()
    start_time = end_time - timedelta(hours=72)
    df = df[(df.index >= start_time) & (df.index <= end_time)]

    df = df.ffill().bfill()

    # IMPORTANT: match trained model input size (7 features)
    df = df.iloc[:, :7]

    return df

# =======================
# PREPROCESS
# =======================

def preprocess_for_model(df):
    scaler = StandardScaler()
    arr = scaler.fit_transform(df.values)

    sequences = []
    for i in range(len(arr) - SEQ_LENGTH - PRED_HORIZON + 1):
        sequences.append(arr[i : i + SEQ_LENGTH])

    X = np.array(sequences)
    return X

# =======================
# RUN PREDICTION
# =======================

def run_prediction():

    df = build_time_series()

    latest_speed = float(df["speed"].iloc[-1])
    latest_density = float(df["density"].iloc[-1])
    latest_bz = float(df["bz_gsm"].iloc[-1])

    if df.shape[0] < (SEQ_LENGTH + PRED_HORIZON):
        print("Not enough real-time data yet")
        return

    X = preprocess_for_model(df)

    model = load_model(MODEL_PATH)

    preds = model.predict(X)

    # mean prediction as storm metric
    storm_value = float(np.mean(preds))

    print("Real-time storm prediction:", storm_value)

    # -------------------------
    # CONFIDENCE CALCULATION
    # -------------------------
    if storm_value > -20:
        confidence = 95
    elif storm_value > -50:
        confidence = 90
    elif storm_value > -100:
        confidence = 85
    else:
        confidence = 80

    # -------------------------
    # SAVE OUTPUT CSV
    # -------------------------
    out_df = pd.DataFrame({
        "storm_value": [round(storm_value, 3)],
        "solar_wind_speed": [round(latest_speed, 2)],
        "density": [round(latest_density, 2)],
        "bz": [round(latest_bz, 2)],
        "confidence": [confidence]
    })

    out_df.to_csv(OUT_CSV, index=False)
    print("Saved real-time to:", OUT_CSV)

    # -------------------------
    # SAVE HISTORY
    # -------------------------
    now = datetime.now().strftime("%d %b %Y %I:%M %p")

    with open(HISTORY_CSV, "a") as hf:
        hf.write(f"{now},{storm_value}\n")

    print("History updated.")

# =======================
# MAIN
# =======================

if __name__ == "__main__":
    run_prediction()
