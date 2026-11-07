# Delhi AQI 48-hour outlook: research prototype.   Run locally with:  streamlit run app.py
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="Delhi AQI 48-hour outlook", layout="wide")


@st.cache_resource
def load_models():
    models = joblib.load(ROOT / "models" / "frozen_models.joblib")
    meta = json.load(open(ROOT / "models" / "frozen_models.json"))
    return models, meta


@st.cache_data
def load_data():
    daily = pd.read_csv(ROOT / "app_data" / "daily_winter.csv", index_col=0, parse_dates=True)
    hourly = pd.read_csv(ROOT / "app_data" / "hourly_small.csv", index_col=0, parse_dates=True)
    return daily, hourly


models, meta = load_models()
cols = meta["features"]
daily, hourly = load_data()

# Historical average rates, for context next to every prediction
below = daily[daily["AQI"] < 301].dropna(subset=["AQI_at_plus_48h"])
above = daily[daily["AQI"] >= 301].dropna(subset=["AQI_at_plus_48h"])
onset_rate = (below["AQI_at_plus_48h"] >= 301).mean()
clear_rate = (above["AQI_at_plus_48h"] < 301).mean()


def category(aqi):
    if pd.isna(aqi):
        return "no reading"
    for upper, name in [(50, "Good"), (100, "Satisfactory"), (200, "Moderate"),
                        (300, "Poor"), (400, "Very Poor")]:
        if aqi <= upper:
            return name
    return "Severe"


def live_outlook(aqi, date, temp, rh, wind):
    d = pd.Timestamp(date)
    start_year = d.year if d.month >= 11 else d.year - 1
    row = pd.DataFrame([{"AQI": aqi, "season_day": (d - pd.Timestamp(start_year, 11, 1)).days,
                         "AT (°C)": temp, "RH (%)": rh, "WS (m/s)": wind}])[cols]
    if aqi < 301:
        return {"mode": "onset",
                "exact": float(models["target_48h_301"].predict_proba(row)[0, 1]),
                "any": float(models["target_any_48h_301"].predict_proba(row)[0, 1])}
    return {"mode": "exit", "clear": float(models["clear_48h"].predict_proba(row)[0, 1])}


st.title("Delhi AQI: 48-hour outlook")
st.warning("Research prototype. Not an official forecast and not health advice. "
           "For real alerts use CPCB (cpcb.nic.in), CAQM (caqm.nic.in) or IITM (tropmet.res.in).")
st.caption("This tool does **not** predict an AQI number. From a 4 PM reading it estimates the chance "
           "that Delhi's AQI reaches 301 (Very Poor) within 48 hours, or, if it is already 301 or above, "
           "the chance it falls below 301.")

tab1, tab2, tab3 = st.tabs(["Replay a past winter day", "Outlook from today's reading", "About and limits"])

# ------------------------------------------------------------------ tab 1
with tab1:
    st.write("Pick any winter day (November to February, 2018 onward). You will see the model's 4 PM outlook "
             "for that day, what actually happened over the next 48 hours, and the weather around it.")
    st.info("The outlook shown here comes from models that did **not** learn from that winter, "
            "so it is an honest look back. It is still a single day: look at the evidence in the paper "
            "or README before reading anything into one case.")
    default_day = daily.index[min(60, len(daily) - 1)].date()
    day = st.date_input("Date", value=default_day,
                        min_value=daily.index.min().date(), max_value=daily.index.max().date())
    t = pd.Timestamp(day) + pd.Timedelta(hours=16)

    if t not in daily.index or pd.isna(daily.loc[t, "AQI"]):
        st.info("No usable 4 PM reading for that date. The data covers November to February only, and a few "
                "days (including November 2020 to February 2021) are left out because of source-data checks.")
    else:
        r = daily.loc[t]
        window_hours = hourly.loc[t + pd.Timedelta(hours=1): t + pd.Timedelta(hours=48)]
        left, mid, right = st.columns(3)
        with left:
            st.subheader("At 4 PM")
            st.metric("AQI", f"{r['AQI']:.0f}", category(r["AQI"]), delta_color="off")
            st.write(f"Temperature {r['AT (°C)']:.1f} °C · humidity {r['RH (%)']:.0f}% · wind {r['WS (m/s)']:.1f} m/s")
        with mid:
            st.subheader("Model outlook")
            if r["AQI"] < 301 and pd.notna(r["risk_exact"]):
                st.metric("Reach 301 exactly at +48h", f"{r['risk_exact']:.0%}")
                st.metric("Reach 301 at any hour in 48h", f"{r['risk_any']:.0%}")
                st.caption(f"Historical average for days starting below 301: {onset_rate:.0%}")
            elif r["AQI"] >= 301 and pd.notna(r["chance_clear"]):
                st.metric("Chance of being below 301 at +48h", f"{r['chance_clear']:.0%}")
                st.caption(f"Historical average for days starting at 301+: {clear_rate:.0%}")
            else:
                st.write("No outlook available for this day.")
        with right:
            st.subheader("What happened")
            a48 = r["AQI_at_plus_48h"]
            st.metric("AQI 48 hours later", "n/a" if pd.isna(a48) else f"{a48:.0f}", category(a48), delta_color="off")
            if window_hours["AQI"].notna().any():
                st.write(f"Highest AQI in the next 48h: {window_hours['AQI'].max():.0f}")
            rain = window_hours["RF (mm)"].sum(min_count=1)
            st.write("Rain in the next 48h: " + ("no data" if pd.isna(rain) else f"{rain:.1f} mm (station average)"))

        win = hourly.loc[t - pd.Timedelta(days=5): t + pd.Timedelta(days=3)]
        fig, ax = plt.subplots(figsize=(10, 3.4))
        ax.plot(win.index, win["AQI"], color="tab:red", linewidth=1.6)
        ax.axhline(301, color="gray", linestyle="--", linewidth=1)
        ax.text(win.index.min(), 305, "301 (Very Poor)", fontsize=8, color="gray")
        ax.axvline(t, color="black", linewidth=1)
        ax.axvspan(t, t + pd.Timedelta(hours=48), color="tab:blue", alpha=0.08)
        ax.text(t, ax.get_ylim()[1] * 0.97, " forecast time, 4 PM", fontsize=8, va="top")
        ax.set_ylabel("AQI"); ax.set_title("Hourly AQI around the day (shaded: the 48 hours being forecast)")
        fig.autofmt_xdate(); fig.tight_layout()
        st.pyplot(fig)

        fig2, axes = plt.subplots(4, 1, figsize=(10, 6), sharex=True)
        for ax_, (col, lab) in zip(axes[:3], [("AT (°C)", "Temp (°C)"), ("RH (%)", "Humidity (%)"),
                                              ("WS (m/s)", "Wind (m/s)")]):
            ax_.plot(win.index, win[col], linewidth=1.2); ax_.set_ylabel(lab)
        axes[3].bar(win.index, win["RF (mm)"].fillna(0), width=0.04, color="tab:blue")
        axes[3].set_ylabel("Rain (mm/h)")
        for ax_ in axes:
            ax_.axvline(t, color="black", linewidth=0.8)
        fig2.autofmt_xdate(); fig2.tight_layout()
        st.pyplot(fig2)

        st.subheader("How unusual was that 4 PM?")
        rows = []
        for col, lab in [("AQI", "AQI"), ("AT (°C)", "Temperature"), ("RH (%)", "Humidity"), ("WS (m/s)", "Wind speed")]:
            pct = (daily[col].dropna() <= r[col]).mean() if pd.notna(r[col]) else np.nan
            rows.append({"measure": lab, "value": round(float(r[col]), 1) if pd.notna(r[col]) else np.nan,
                         "percentile among winter 4 PM readings": None if pd.isna(pct) else f"{pct:.0%}"})
        st.table(pd.DataFrame(rows).set_index("measure"))
        st.caption("In the models, at the same AQI, colder and calmer conditions and earlier days in the winter went with "
                   "higher risk of reaching 301. These are associations in past data, not proven causes.")

# ------------------------------------------------------------------ tab 2
with tab2:
    st.write("Enter today's 4 PM AQI and weather. The outlook covers the next 48 hours only; there is no "
             "prediction for dates further ahead.")
    c1, c2 = st.columns(2)
    with c1:
        aqi_in = st.number_input("AQI at 4 PM today", 0, 500, 240)
        date_in = st.date_input("Today's date", pd.Timestamp.today().date(), key="live_date")
    with c2:
        temp_in = st.number_input("Temperature (°C)", -5.0, 45.0, 18.0)
        rh_in = st.number_input("Relative humidity (%)", 0.0, 100.0, 55.0)
        wind_in = st.number_input("Wind speed (m/s)", 0.0, 10.0, 1.0)

    if pd.Timestamp(date_in).month in (3, 4, 5, 6, 7, 8, 9, 10):
        st.info("The models were trained only on November to February days, so results outside those months are unreliable.")
    out = live_outlook(aqi_in, date_in, temp_in, rh_in, wind_in)
    st.write(f"Today's AQI category: **{category(aqi_in)}**")
    if out["mode"] == "onset":
        a, b = st.columns(2)
        a.metric("Reach 301 exactly at +48 hours", f"{out['exact']:.0%}")
        b.metric("Reach 301 at any hour within 48 hours", f"{out['any']:.0%}")
        st.caption(f"Historical average for days starting below 301: {onset_rate:.0%}. This is a probability, not an alarm.")
    else:
        st.metric("Chance AQI is below 301 in 48 hours", f"{out['clear']:.0%}")
        st.caption(f"Historical average for days starting at 301+: {clear_rate:.0%}. "
                   "In past data, rain in the next two days went with much higher chances of clearing. "
                   "The model does not know the rain forecast, so check IMD's forecast too.")

# ------------------------------------------------------------------ tab 3
with tab3:
    st.markdown(f"""
**What this is.** A small research prototype from a study of Delhi winters (CPCB hourly city AQI and six-station
pollution and weather data, 2018 onward). It uses logistic regression on five inputs: AQI at 4 PM, day of winter,
temperature, humidity and wind speed. Models were frozen on {meta['frozen_on']}.

**What it is not.** It is not an AQI value forecast, not an official forecast, and not health advice. It covers
48 hours ahead, November to February only, and city-level AQI.

**How well it works.** On winter 2025–26, the exit model scored AUC 0.80 on 90 eligible days, including 20 clearances;
its day-resampling range was 0.69–0.90. This is exploratory evidence: the exit task was added after the onset analysis,
and that winter was included in the full-period rainfall diagnostic. Predictions of new onsets were inconclusive on
the small holdout. Confirm the exit result with a later prospective winter. A fixed onset alert cutoff did not transfer
reliably between winters, so this prototype shows probabilities. See the README and paper.

**Data.** Central Pollution Control Board (CPCB) public data. Part of the 2021 city workbook disagreed with CPCB bulletins and
was excluded.
""")
