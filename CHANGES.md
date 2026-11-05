# Project Change Log

## 2026 data update and notebook refresh

### Data added or checked

- Added the available 2026 CPCB city-level AQI workbooks under `aqi_target/2026/` (January–September). Notebook 01 skips months without a workbook, so October–December do not stop the run.
- Checked the six station folders for 2026 hourly data. Each existing station file covers January 1–September 30, 2026.
- Downloaded fresh 2026 hourly exports from the CPCB repository and compared SHA-256 hashes with the files already in `raw_data/`; all six matched. No duplicate raw files were retained.
- The annual-average AQI chart omits partial 2021 and 2026. Daily and monthly charts include available 2026 data and are labeled as partial-year coverage.

### Notebook changes

- **Notebook 01:** extended the AQI and station-data year range through 2026; added a skip for unavailable AQI months; saves the combined source as `delhi_6station_avg_2018_2026.csv`.
- **Notebook 02:** loads and saves the 2018–2026 analysis data; includes winter-start year 2025 (winter 2025–26); updates the chronological train/validation/test split; keeps partial years out of annual comparisons.
- **Notebook 02 startup fix:** detects the repository root and switches to `notebooks/` before relative-path operations. This resolves VS Code plot-save failures when the kernel starts at the repository root; verified by running Notebook 02 from that launch directory.
- **Notebook 02 target definitions:** exact future 4 PM AQI threshold outcomes already covered +24h, +48h, and +72h. Added the matching any-hour AQI ≥301 outcomes within each of those windows. A positive requires an observed threshold crossing; a negative requires a complete observed window; otherwise the outcome remains unknown.
- **Notebook 03:** evaluates the compact logistic model on all six target/horizon combinations. Target columns remain excluded from model features. The 48-hour cutoffs remain 0.3 for the exact endpoint and 0.4 for the any-hour outcome; no alert cutoffs were assigned to the new 24-hour or 72-hour outcomes.
- Updated notebook Markdown and the README to describe the partial 2026 coverage, the winter split, and all six outcomes. No notebook cells were added.

### Current test-winter scores

Notebook 03 evaluated winter 2025–26. Eligible rows start below AQI 301 and have a known outcome. Scores use the same compact model; AP and AUC uncertainty ranges are saved in the notebook and use day resampling.

| Outcome | Eligible days (positive forecast days) | Average precision | ROC AUC | Brier |
|---|---:|---:|---:|---:|
| Exact +24h | 28 (12) | 0.52 | 0.51 | 0.274 |
| Exact +48h | 28 (19) | 0.77 | 0.60 | 0.291 |
| Exact +72h | 27 (18) | 0.83 | 0.65 | 0.273 |
| Any hour within +24h | 28 (16) | 0.63 | 0.53 | 0.318 |
| Any hour within +48h | 28 (23) | 0.93 | 0.70 | 0.259 |
| Any hour within +72h | 28 (26) | 0.96 | 0.56 | 0.216 |

These are positive **forecast days**, not independent AQI onsets. The any-hour +72h outcome is positive on 26 of 28 eligible days, so its high AP should be interpreted alongside its ROC AUC and prevalence.

### Generated and verified outputs

- Re-ran Notebook 01, Notebook 02, and Notebook 03 with the 2026 data; after adding the three any-hour labels, reran Notebooks 02 and 03.
- The updated notebooks have no execution errors. The 2026 processed source and cleaned files, winter labels, onset list, and EDA plots were regenerated.
- Exact and any-hour labels are excluded from the feature inputs to prevent target leakage.

## Files updated or regenerated

- `README.md`
- `notebooks/01_explore_data.ipynb`
- `notebooks/02_eda_data.ipynb`
- `notebooks/03_baselines_and_models.ipynb`
- `processed_data/delhi_6station_avg_2018_2026.csv`
- `processed_data/delhi_6station_avg_2018_2026_cleaned.csv`
- `processed_data/daily_4pm_winter_labels.csv`
- `processed_data/winter_onsets.csv`
- EDA plots under `eda_plots/`

2026 AQI source coverage is January–September only. The 2025–26 winter test is small, with 27–28 eligible forecast days per outcome; interpret its scores as limited evidence rather than a broad operational validation.

## Winter 2020–21 inclusion sensitivity

- Clarified in Notebooks 01 and 02 and the README that the January–February 2021 CPCB AQI discrepancy against the PM-derived proxy is unresolved; it does not establish that the official AQI values are wrong. The original source values remain unchanged.
- Compared the locked five-feature compact logistic model with and without winter 2020–21 added to training, using six-winter out-of-fold evaluation and the existing 2024–25 validation winter. The 2025–26 holdout was excluded from this comparison and was not rerun.
- Winter 2020–21 contributed 44 eligible daily forecasts for each 48-hour outcome: 23 positives for the exact +48h target and 29 for the any-hour target.
- Results were mixed. In pooled out-of-fold forecasts, exact +48h AP/AUC/Brier changed from 0.738/0.854/0.140 to 0.732/0.846/0.144; any-hour +48h changed from 0.766/0.812/0.171 to 0.774/0.806/0.175. At the locked cutoffs, false alarms increased from 64 to 73 for exact +48h and from 53 to 59 for any-hour +48h. The 2024–25 validation scores also worsened with inclusion.
- Kept winter 2020–21 out of the primary training split and documented the comparison as a sensitivity analysis in Notebook 03. This preserves the already evaluated model and avoids using the test winter to choose a revised training set.

## Rainfall and AQI change diagnostic

- Added a descriptive rainfall diagnostic to Notebook 03 using realized `RF (mm)` summed over hours +1 through +48. A day is included when at least 40 of the 48 rainfall hours are observed. `TOT-RF (mm)` is not used.
- The table includes 840 usable forecast days from winters 2018–19 and 2021–26, including 118 days from winter 2025–26. It separates days starting at AQI 301 or above from days starting below 301 and reports clearance/onset shares plus mean AQI change by rainfall bin.
- In the current project files, 502 days start at AQI 301 or above and 338 start below it. For high-start days, the clearance share was 19% with no rain (431 days), 50% under 1 mm (52 days), 79% at 1–5 mm (14 days), and 80% over 5 mm (5 days). Counts in the rainier groups are small; this is association, not a causal estimate or a forecast result.
- This differs from the earlier supplied table's 781 usable days. The Notebook 03 cell records the reproducible counts from the current cleaned hourly file and current daily forecast table; resolve the sample/filter discrepancy before using either set of numbers in a paper.

## Publication-strengthening analysis in Notebook 03

- Added an expanding chronological backtest: each development winter is predicted using only earlier winters. The 2025–26 test winter is excluded. Added pooled Brier skill against a training-prevalence reference and 7-day block-bootstrap ranges for the two primary 48-hour outcomes. These are development estimates across five chronological folds, not a replacement independent test.
- Added calibration plots for the exact and any-hour 48-hour outcomes using chronological predictions. With the small number of winters and binned points, treat these plots and bootstrap ranges as descriptive uncertainty checks.
- Corrected event-level warning metrics to use the chronological predictions instead of leave-one-winter-out predictions, which can train on later winters. Through winter 2024–25, the any-hour 48-hour model at risk 0.4 has a usable forecast window for 43 onsets, warns before 37, misses 6 covered onsets, and has a median first-warning lead of 28 hours. It forms 56 alert episodes, 22 with no onset in their next 48-hour forecast windows. These are distinct from positive forecast-day counts and are not test-winter results.
- The starting-AQI band table now reports caught positive forecast days; it does not claim to count unique events. In the chronological evaluation, the any-hour 48-hour model warns on 10/74 days below AQI 200, 29/66 days from 200–249, and 83/107 days from 250–300. Read the alerts and outcome counts together; these are daily observations, not independent events.
- `TOT-RF (mm)` is excluded defensively if present, and the rainfall diagnostic uses `RF (mm)` only. The current daily modeling frame did not include `TOT-RF` in its feature list, so this exclusion did not change prior candidate scores. Comparisons were refreshed with the current feature frame.
- Added a short publication-positioning note and examples of existing Delhi AQI/PM forecast papers to the README. This is not a completed systematic literature review or a novelty assessment.
- The 840-versus-781 rainfall diagnostic sample discrepancy remains unresolved. The rainfall analysis is descriptive and includes winter 2025–26; no rainfall/oracle model was fit or tuned on that test winter.
- Refreshed all Notebook 03 development outputs after the event-analysis update. Preserved the saved Cell B 2025–26 test output and did not rerun it or use it to change the model or thresholds.
- The 2025–26 test cell still reports its existing day-resampling ranges; they remain approximate for serially correlated days. The weekly-block ranges currently apply to the chronological development backtest, not the sealed test result.

## Reviewer-facing interpretation clarifications

- Designated exact +48-hour AQI ≥301 crossing from a starting AQI below 301 as the single primary outcome, consistent with the original research question. Any-hour +48h is secondary; 24h and 72h variants are exploratory secondary outcomes.
- Clarified that the historical 80% alert-cutoff rule counted positive forecast days, not unique onset events. Notebook and README now keep forecast-day counts, onset counts, and warning episodes distinct.
- Updated the README to state that the primary test result did not beat the AQI ≥250 reference on positive forecast-day capture (12/19 vs 13/19), that the secondary any-hour difference is small (16/23 vs 15/23), and that these small counts do not establish operational reliability.
- Added that the forecasts use observed issue-time inputs and their reporting latency has not been checked. No claim of a real-time warning service is made.
- Documented that choosing the compact model was a parsimony decision based on score comparisons; no paired uncertainty test established equivalence to the all-columns model.
- These changes clarify the research question and interpretation only. The model, cutoff values, 2025–26 test scores, and saved test outputs were not changed or rerun.
