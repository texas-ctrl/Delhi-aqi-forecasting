# Delhi AQI Forecasting — Project Handoff

## Project purpose

This is a student internship-portfolio and research project using Delhi air-quality data. The current research direction is to study and eventually forecast **hourly AQI threshold events**. Modeling/training has **not started**; the present stage is data exploration, EDA, literature review, and target-definition work.

## Data and notebooks

- The selected analysis period is **2018–2025**. There is no 2017 analysis year.
- The sensor data comes from six monitoring stations: Anand Vihar, Rohini, RK Puram, Punjabi Bagh, ITO, and Okhla.
- `notebooks/01_explore_data.ipynb` loads the AQI workbooks for each month and year, reads sensor CSVs, filters to 2018–2025, averages numeric station readings by timestamp, joins city-level AQI, and saves `processed_data/delhi_6station_avg_2018_2025.csv`.
- The loader has a fallback for Excel files whose downloaded name contains a suffix such as `(1)`.
- `notebooks/02_eda_data.ipynb` uses the 2018–2025 processed data and explores AQI trends, missingness, pollutant relationships, time lags, winter patterns, threshold-event prevalence, and feature preparation.
- The regenerated hourly table contains 70,128 timestamps (the full hourly grid for 2018–2025, including leap year 2024). AQI is missing for 571 timestamps; other sensor features also have missing values.

## EDA observations recorded so far

- AQI is strongly correlated with PM2.5 (about 0.75) and PM10 (about 0.75) across the full series.
- AQI has strong short-term persistence: correlations with AQI 24, 48, and 72 hours earlier are approximately 0.90, 0.83, and 0.79.
- Across daily winter means, PM2.5 and PM10 remain strongly associated with AQI; wind speed has a negative association. These are exploratory relationships, not evidence of cause.
- The current event rule is project-defined: AQI is at most 250 at the prediction time and at least 301 at the exact future timestamp. The notebook's 48-hour and 72-hour labels check AQI exactly at `t+48h` or `t+72h`; they do **not** check whether a threshold is crossed at any time during the interval.
- With that rule, the saved notebook results show positive rates of about 2.20% (48-hour) and 2.74% (72-hour) across all hours; in winter they are about 4.11% and 5.35%.
- The hourly values are highly similar across adjacent hours (lag-1 correlation about 0.9993). This may reflect smoothing, but the local data alone does not establish how the source calculated each hourly value.
- There is an interpretation mismatch to revisit: notebook prose says wind is lower before 48-hour events, but the saved group means show 0.816 m/s for event rows and 0.780 m/s for non-event rows. The t-test is significant, but that comparison does not support the written direction.
- Complete-case filtering in the later preparation cells reduces the training-period rows from 14,316 to 4,155. That loss should be addressed before any model training; any imputation must be fitted on training data only.

## Visual and cleanup changes

- The daily trend plot's x-axis now labels years instead of repeating every month name across the eight-year chart.
- The EDA plot-saving code now saves the monthly trend, monthly boxplot, and yearly-average chart to their own matching image filenames.
- The `eda_plots` images were taken from actual notebook chart outputs.
- The obsolete 2022–2025 cleaned CSV is being removed from the tracked GitHub files. Corrected 2024 AQI source workbooks are included so GitHub has the inputs that produced the accepted 2024 results. The added 2018–2021 AQI workbooks, sensor CSVs, and generated 2018–2025 processed CSVs remain local and are not included in this update.
- Notebook prose and comments now describe the event rule with the project's AQI thresholds, without claiming an official policy action.

## Related work reviewed

- [VayuAnukulani](https://arxiv.org/abs/1904.03977): Delhi CPCB and weather data at five locations; forecasts pollutant levels up to 24 hours and compares against baselines.
- [DELFI](https://arxiv.org/abs/2210.15923): Delhi-NCR PM2.5 forecasting across 13 stations; explores probabilistic forecasts and reports limitations of long-horizon point predictions.
- [CEEW's Delhi forecast evaluation](https://www.ceew.in/sites/default/files/ceew-how-well-can-delhi-predict-air-quality.pdf): evaluates operational forecast categories and pollutant concentrations and uses event-detection measures such as detection and false-alarm rates.
- [IITM Delhi Air Quality Early Warning System](https://ews.tropmet.res.in/index-2.php): an operational hourly air-quality forecast up to 72 hours; historical issue-time forecasts would be needed for a fair past-period comparison.
- [AirCast](https://github.com/Manglam11/air_cast) and [Delhi-NCR air-quality forecasting](https://github.com/RakeshSainiDelhi42/delhi-ncr-air-quality-forecasting): code references for gap-aware preprocessing, explicit data-quality reporting, simple baselines, and time-respecting backtests. These repositories are design examples, not proof that their results transfer to this project.

No exact match was established by this initial search. A broader literature review is needed before making a research-novelty claim.

## Agreed direction and next steps

1. Continue with the hourly series; do not switch the main study to daily AQI.
2. Before modeling, decide whether the event means a crossing at one exact future hour or any crossing within a defined future window.
3. Audit timestamp gaps, missing AQI, station coverage, and how the source labels the hourly AQI values. Keep incomplete target periods visible rather than silently filling them.
4. Correct the wind-speed interpretation and check that all plot filenames match their chart code and notebook outputs.
5. Finish the literature review and write down the target, horizon, and evaluation plan in plain language.
6. Only after those decisions, begin baseline evaluation and then model training with chronological validation. No model has been trained as part of this work.
