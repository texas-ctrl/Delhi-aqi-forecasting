"""
Full EDA pipeline on the expanded dataset (2018-2025).

AQI source:
  - 2018-2023: official CPCB city-level xlsx files
  - 2021 Oct/Nov/Dec: missing from portal (handled cleanly as gaps)
  - 2024 & 2025: computed consistently from multi-station raw PM2.5 using official CPCB formula

Saves:
  processed_data/delhi_6station_avg_2018_2025.csv
  processed_data/delhi_6station_avg_2018_2025_cleaned.csv
  processed_data/modeling_data.pkl
  eda_plots/
"""

import glob, os, warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT     = r"c:\Users\Deepak\Desktop\aqi-forecasting"
RAW_DIR  = os.path.join(ROOT, "raw_data")
AQI_DIR  = os.path.join(ROOT, "aqi_target")
PROC_DIR = os.path.join(ROOT, "processed_data")
PLOT_DIR = os.path.join(ROOT, "eda_plots")
os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

STATIONS   = ["anand_vihar","rohini","rk_puram","punjabi_bagh","ito","okhla"]
XLSX_YEARS = list(range(2018, 2024))   # 2018-2023 official xlsx AQI
RAW_YEARS  = list(range(2018, 2026))   # 2018-2025 sensor CSVs
MONTHS = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
          7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}

# CPCB official PM2.5 -> AQI breakpoints (24h average, ug/m3)
PM25_BP = [
    (0,   30,  0,   50),
    (31,  60,  51,  100),
    (61,  90,  101, 200),
    (91,  120, 201, 300),
    (121, 250, 301, 400),
    (251, 500, 401, 500),
]

def pm25_to_aqi(val):
    if pd.isna(val) or val < 0:
        return np.nan
    for bplo, bphi, ilo, ihi in PM25_BP:
        if bplo <= val <= bphi:
            return round(((ihi - ilo) / (bphi - bplo)) * (val - bplo) + ilo)
    return 500

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 – Load raw station data (2018-2025)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 - Loading raw station data (2018-2025) ...")

station_dfs = []
for station in STATIONS:
    files = glob.glob(os.path.join(RAW_DIR, station, "*.csv"))
    dfs = []
    for f in files:
        yr = int(os.path.basename(f).split("_")[2])
        if yr not in RAW_YEARS:
            continue
        d = pd.read_csv(f)
        d["Timestamp"] = pd.to_datetime(d["Timestamp"], format="mixed", dayfirst=True)
        dfs.append(d)
    if not dfs:
        print(f"  WARNING: no files for {station}")
        continue
    sdf = pd.concat(dfs).sort_values("Timestamp").reset_index(drop=True)
    sdf["station"] = station
    station_dfs.append(sdf)
    print(f"  {station}: {len(sdf):,} rows")

all_stations = pd.concat(station_dfs, ignore_index=True)
numeric_cols = all_stations.select_dtypes(include="number").columns
city_avg = all_stations.groupby("Timestamp")[numeric_cols].mean().reset_index()
print(f"\nCity average shape: {city_avg.shape}")
print(f"Date range: {city_avg['Timestamp'].iloc[0]} to {city_avg['Timestamp'].iloc[-1]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – Load official AQI for 2018-2023
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 2 - Loading official AQI xlsx (2018-2023) ...")

aqi_all = []
for year in XLSX_YEARS:
    for num, name in MONTHS.items():
        fpath = os.path.join(AQI_DIR, str(year),
                             f"AQI_Data_City_Level_Delhi_{name}_{year}_Hourly.xlsx")
        if not os.path.exists(fpath):
            print(f"  MISSING: {os.path.basename(fpath)}")
            continue
        df = pd.read_excel(fpath)
        long = df.melt(id_vars="Date", var_name="Hour", value_name="AQI")
        hour_clean = long["Hour"].astype(str).str[:5]
        long["Timestamp"] = pd.to_datetime(
            f"{year}-{num:02d}-" + long["Date"].astype(str).str.zfill(2)
            + " " + hour_clean, format="%Y-%m-%d %H:%M", errors="coerce")
        long = long.dropna(subset=["Timestamp"])
        aqi_all.append(long[["Timestamp","AQI"]])

aqi_xlsx = pd.concat(aqi_all).sort_values("Timestamp").reset_index(drop=True)
print(f"xlsx AQI rows: {len(aqi_xlsx):,}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – Compute AQI for 2024 & 2025 from raw PM2.5
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 3 - Computing AQI for 2024 & 2025 from raw PM2.5 ...")

pm_col = next(c for c in city_avg.columns if "PM2.5" in c)
city_avg_ts = city_avg.set_index("Timestamp").sort_index()

# 24-hour rolling average of PM2.5 for 2024 and 2025
city_computed_years = city_avg_ts[city_avg_ts.index.year.isin([2024, 2025])]
pm25_24h = city_computed_years[pm_col].rolling(24, min_periods=18).mean()
aqi_computed = pm25_24h.apply(pm25_to_aqi).reset_index()
aqi_computed.columns = ["Timestamp", "AQI"]
aqi_computed = aqi_computed.dropna(subset=["AQI"])
print(f"Computed 2024+2025 AQI rows: {len(aqi_computed):,}")
print(f"2024+2025 AQI stats: mean={aqi_computed['AQI'].mean():.1f}  min={aqi_computed['AQI'].min():.0f}  max={aqi_computed['AQI'].max():.0f}")

# Combine xlsx AQI (2018-2023) + computed AQI (2024-2025)
aqi_df = pd.concat([aqi_xlsx, aqi_computed]).sort_values("Timestamp").reset_index(drop=True)
print(f"\nTotal AQI rows: {len(aqi_df):,}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 – Merge sensor average with AQI
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 4 - Merging ...")

final = pd.merge(
    city_avg.set_index("Timestamp"),
    aqi_df.set_index("Timestamp"),
    left_index=True, right_index=True, how="inner",
)
final.index.name = "Timestamp"
print(f"Merged shape: {final.shape}")

raw_path = os.path.join(PROC_DIR, "delhi_6station_avg_2018_2025.csv")
final.to_csv(raw_path)
print(f"Saved: {raw_path}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 – EDA plots
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 5 - EDA plots ...")

# 5a – Daily AQI trend
fig, ax = plt.subplots(figsize=(18, 5))
final["AQI"].resample("D").mean().plot(ax=ax)
ax.set_title("Delhi Daily Average AQI, 2018-2025")
ax.set_ylabel("AQI")
ax.set_xlabel("Date")
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.xticks(rotation=45)
plt.yticks(range(0, 551, 50))
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "01_daily_aqi_trend.png"), dpi=120)
plt.close()
print("  saved 01_daily_aqi_trend.png")

# 5b – AQI histogram
fig, ax = plt.subplots(figsize=(10, 5))
final["AQI"].plot(kind="hist", bins=50, ax=ax, edgecolor="black", alpha=0.8)
ax.set_title("Distribution of Delhi AQI (2018-2025)")
ax.set_xlabel("AQI")
ax.set_ylabel("Frequency")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "02_aqi_histogram.png"), dpi=120)
plt.close()
print("  saved 02_aqi_histogram.png")

# 5c – Monthly AQI trend
fig, ax = plt.subplots(figsize=(14, 5))
final["AQI"].resample("ME").mean().plot(ax=ax)
ax.set_title("Monthly Average Delhi AQI, 2018-2025")
ax.set_xlabel("Date")
ax.set_ylabel("Average AQI")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "03_monthly_aqi_trend.png"), dpi=120)
plt.close()
print("  saved 03_monthly_aqi_trend.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 – Missing values & cleaning
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 6 - Missing values ...")

print("Before cleaning:")
print(final.isnull().sum().to_string())

final = final.dropna(axis=1, thresh=len(final) * 0.10)
final = final.fillna(final.median(numeric_only=True))

print("\nAfter cleaning - all NaN: ", final.isnull().sum().sum())

cleaned_path = os.path.join(PROC_DIR, "delhi_6station_avg_2018_2025_cleaned.csv")
final.to_csv(cleaned_path)
print(f"Saved: {cleaned_path}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 – PM2.5 vs PM10
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 7 - PM2.5 vs PM10 ...")

pm_cols = [c for c in final.columns if ("PM2.5" in c or "PM10" in c) and "_" not in c.split("PM")[1][:5]][:2]
fig, ax = plt.subplots(figsize=(14, 5))
final[pm_cols].resample("ME").mean().plot(ax=ax)
ax.set_title("Monthly Average PM2.5 vs PM10, 2018-2025")
ax.set_xlabel("Date")
ax.set_ylabel("Concentration")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "04_pm25_pm10_monthly.png"), dpi=120)
plt.close()
print("  saved 04_pm25_pm10_monthly.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 – Correlation with AQI
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 8 - Correlation with AQI ...")

corr = final.corr()["AQI"].sort_values(ascending=False)
print(corr.to_string())

fig, ax = plt.subplots(figsize=(10, 7))
corr.drop("AQI").sort_values().plot(kind="barh", ax=ax)
ax.set_title("Feature Correlation with AQI")
ax.set_xlabel("Pearson r")
ax.axvline(0, color="black", linewidth=0.8)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "05_correlation_with_aqi.png"), dpi=120)
plt.close()
print("  saved 05_correlation_with_aqi.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 – AQI lag correlations
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 9 - AQI lag correlations ...")

final["AQI_24h"] = final["AQI"].shift(24)
final["AQI_48h"] = final["AQI"].shift(48)
final["AQI_72h"] = final["AQI"].shift(72)

lag_corr = final[["AQI","AQI_24h","AQI_48h","AQI_72h"]].corr()["AQI"]
print(lag_corr.to_string())

# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 – Future AQI & winter weather
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 10 - Winter weather vs future AQI ...")

final["AQI_24h_ahead"] = final["AQI"].shift(-24)
final["AQI_48h_ahead"] = final["AQI"].shift(-48)
final["AQI_72h_ahead"] = final["AQI"].shift(-72)

winter = final[final.index.month.isin([11, 12, 1, 2])].copy()

ws_col = next((c for c in final.columns if c.startswith("WS") and "(" in c), None)
met_cols = [c for c in ["WS (m/s)","AT (°C)","RH (%)","WD (deg)","BP (mmHg)","SR (W/mt2)","RF (mm)","TOT-RF (mm)"]
            if c in winter.columns]

for horizon, col in [("24h","AQI_24h_ahead"),("48h","AQI_48h_ahead"),("72h","AQI_72h_ahead")]:
    c = winter[met_cols + [col]].corr()[col].sort_values(ascending=False)
    print(f"\nWinter weather -> AQI {horizon}:")
    print(c.to_string())

if ws_col:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(winter[ws_col], winter["AQI_48h_ahead"], alpha=0.15, s=5)
    ax.set_xlabel("Wind Speed (m/s)")
    ax.set_ylabel("AQI 48h ahead")
    ax.set_title("Winter: Wind Speed vs AQI 48h ahead (2018-2025)")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "06_wind_vs_aqi48h.png"), dpi=120)
    plt.close()
    print("\n  saved 06_wind_vs_aqi48h.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 11 – AQI change distribution
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 11 - AQI change analysis ...")

final["AQI_change_48h"] = final["AQI_48h_ahead"] - final["AQI"]
final["AQI_change_72h"] = final["AQI_72h_ahead"] - final["AQI"]

for col in ["AQI_change_48h","AQI_change_72h"]:
    print(f"\n{col}:")
    print(final[col].describe().to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, col in zip(axes, ["AQI_change_48h","AQI_change_72h"]):
    final[col].dropna().plot(kind="hist", bins=60, ax=ax, edgecolor="black", alpha=0.8)
    ax.axvline(0, color="red", linewidth=1)
    ax.set_title(f"Distribution of {col}")
    ax.set_xlabel("AQI Change")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "07_aqi_change_distribution.png"), dpi=120)
plt.close()
print("  saved 07_aqi_change_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 12 – Monthly box-plot
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 12 - Monthly AQI box-plot ...")

fig, ax = plt.subplots(figsize=(14, 6))
data_by_month = [final.loc[final.index.month == m, "AQI"].dropna().values for m in range(1, 13)]
ax.boxplot(data_by_month, labels=list(MONTHS.values()), patch_artist=True)
ax.set_title("AQI Distribution by Month (2018-2025)")
ax.set_ylabel("AQI")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "08_aqi_boxplot_by_month.png"), dpi=120)
plt.close()
print("  saved 08_aqi_boxplot_by_month.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 13 – Yearly AQI bar
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 13 - AQI by year ...")

yearly = final["AQI"].groupby(final.index.year).mean().round(1)
print(yearly.to_string())

fig, ax = plt.subplots(figsize=(8, 5))
yearly.plot(kind="bar", ax=ax, edgecolor="black")
ax.set_title("Yearly Average AQI, Delhi (2018-2025)")
ax.set_ylabel("Average AQI")
ax.set_xlabel("Year")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "09_yearly_aqi.png"), dpi=120)
plt.close()
print("  saved 09_yearly_aqi.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 14 – Feature engineering
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 14 - Feature engineering ...")

at_col = next((c for c in final.columns if c.startswith("AT")), None)
if at_col:
    final["Temp_change_24h"] = final[at_col].diff(24)

final["AQI_3d_mean"] = final["AQI"].rolling(72).mean()

pm25_col = next((c for c in final.columns if "PM2.5" in c and "ahead" not in c and "change" not in c and c.count("_") == 0), None)
pm10_col = next((c for c in final.columns if "PM10" in c and "ahead" not in c and "change" not in c and c.count("_") == 0), None)

for col in [c for c in [pm25_col, pm10_col] if c]:
    for lag in [24, 48, 72]:
        final[f"{col}_{lag}h"] = final[col].shift(lag)

ws_raw = next((c for c in final.columns if "WS" in c and "(" in c), None)
if ws_raw:
    for lag in [24, 48, 72]:
        final[f"WS_{lag}h"] = final[ws_raw].shift(lag)

# Wind direction as sine/cosine (circular encoding)
wd_col = next((c for c in final.columns if "WD" in c and "(" in c), None)
if wd_col:
    wd_rad = final[wd_col] * np.pi / 180
    final["WD_sin"] = np.sin(wd_rad)
    final["WD_cos"] = np.cos(wd_rad)

# Crop burning season flag (Oct 15 - Nov 30 = peak Punjab paddy burning)
final["crop_burning"] = (
    ((final.index.month == 10) & (final.index.day >= 15)) |
    (final.index.month == 11)
).astype(int)

# Rolling AQI std (volatility signal)
final["AQI_72h_std"] = final["AQI"].rolling(72).std()

# Time features
final["day_of_week"] = final.index.dayofweek
hour  = final.index.hour
month = final.index.month
final["hour_sin"]  = np.sin(2 * np.pi * hour  / 24)
final["hour_cos"]  = np.cos(2 * np.pi * hour  / 24)
final["month_sin"] = np.sin(2 * np.pi * month / 12)
final["month_cos"] = np.cos(2 * np.pi * month / 12)

print(f"Total features: {final.shape[1]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 15 – Define targets
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 15 - Target definitions ...")

final["target_48h"] = (final["AQI"] < 300) & (final["AQI_48h_ahead"] >= 300)
final["target_72h"] = (final["AQI"] < 300) & (final["AQI_72h_ahead"] >= 300)

for name, col in [("48h","target_48h"),("72h","target_72h")]:
    pct = final[col].mean() * 100
    print(f"  target_{name}: {final[col].sum()} positives ({pct:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 16 – Winter-only model data + chronological split
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 16 - Winter model data & split ...")

winter_model = final[final.index.month.isin([11, 12, 1, 2])].copy()
winter_model = winter_model[winter_model["AQI_change_48h"].notna()]

drop_cols = [
    "AQI_24h_ahead","AQI_48h_ahead","AQI_72h_ahead",
    "AQI_change_48h","AQI_change_72h",
    "target_48h","target_72h",
]
y = winter_model["target_48h"]
X = winter_model.drop(columns=drop_cols, errors="ignore")

# Split: Train 2018-2022 / Val 2023 / Test 2024-2025
train_mask = X.index.year <= 2022
val_mask   = X.index.year == 2023
test_mask  = X.index.year >= 2024

X_train, y_train = X[train_mask], y[train_mask]
X_val,   y_val   = X[val_mask],   y[val_mask]
X_test,  y_test  = X[test_mask],  y[test_mask]

print(f"  Train: {X_train.shape}  positives={y_train.sum()}")
print(f"  Val:   {X_val.shape}   positives={y_val.sum()}")
print(f"  Test:  {X_test.shape}  positives={y_test.sum()}")
print(f"  NaN in X_train: {X_train.isna().sum().sum()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 17 – Save modeling data
# ─────────────────────────────────────────────────────────────────────────────
print("\nSTEP 17 - Saving modeling_data.pkl ...")

model_path = os.path.join(PROC_DIR, "modeling_data.pkl")
final.to_pickle(model_path)
print(f"  Saved: {model_path}  shape={final.shape}")

print("\n" + "=" * 60)
print("ALL STEPS COMPLETE")
print(f"Plots: {PLOT_DIR}")
print(f"Data:  {PROC_DIR}")
