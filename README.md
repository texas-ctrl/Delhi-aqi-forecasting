# Delhi AQI Forecasting

This project studies hourly Delhi AQI and six-station pollutant/weather readings from 2018 through September 2026. The primary analysis uses whole winter seasons and excludes winter 2020–21 (winter-start year 2020), whose January–February 2021 AQI has an unresolved discrepancy with a PM-derived proxy. This is not evidence that the official CPCB values are wrong; Notebook 03 reports a training sensitivity with the unmasked values included.

## Research question

At 4 PM, can a compact model forecast whether Delhi AQI will reach 301 exactly 48 hours later, given that the current AQI is below 301? This exact +48-hour crossing is the **single primary outcome**. Reaching 301 at any hour within 48 hours is secondary; the exact and any-hour 24- and 72-hour outcomes are exploratory secondary analyses. A separate, post-hoc exit analysis asks whether AQI that starts at 301 or above will be below 301 exactly 48 hours later. It is reported separately from the onset task.

## Data

- **AQI target:** CPCB city-level hourly workbooks. The 2026 folder has January–September; unavailable October–December workbooks are skipped. The original AQI values are retained in the source file.
- **Station measurements:** hourly CSVs for Anand Vihar, Rohini, RK Puram, Punjabi Bagh, ITO, and Okhla. Each 2026 station file covers January 1–September 30. These files were already present in the project and matched fresh CPCB downloads.
- **2021 review status:** Notebook 01 marks January–September 2021 as `review_required` and October–December as `crosscheck_consistent`. Notebook 02 masks flagged AQI values in its EDA copy; the source file remains unchanged. The primary forecasting split excludes winter 2020–21, while Notebook 03 compares the locked compact model with and without that winter added to training.
- **Processed data and figures:** generated under `processed_data/` and `eda_plots/` by running Notebooks 01, 02, and 03 in order from the `notebooks/` directory.

The annual-average chart omits partial 2021 and 2026. Monthly and daily plots include the available values and should be read with the 2026 coverage limit in mind.

## Winter splits and locked model

Winter-start years 2018, 2019, and 2021–2025 are included; winter 2020 is excluded. Development uses winters 2018, 2019, 2021, 2022, and 2023; validation uses 2024–25; the final holdout is 2025–26.

The final model was chosen before the new holdout: logistic regression (`C=0.1`) with five inputs—AQI, season day, temperature, humidity, and wind speed. Alert cutoffs remain 0.3 for the exact +48-hour label and 0.4 for the any-hour label.

The compact model was selected for parsimony after comparing cross-winter scores. The comparisons do not include paired uncertainty tests, so they do not establish statistical equivalence to the all-columns model.

Across the six earlier winters in the current cross-winter analysis, the compact model scored:

| Outcome | Average precision | ROC AUC | Brier | Worst-winter AUC |
|---|---:|---:|---:|---:|
| Exact +48h | 0.74 | 0.85 | 0.140 | 0.79 |
| Any hour within 48h | 0.77 | 0.81 | 0.171 | 0.71 |

Winter 2020–21 inclusion sensitivity: the unmasked source adds 44 eligible daily forecasts for each 48-hour outcome (23 exact positives and 29 any-hour positives). On pooled six-winter out-of-fold forecasts, adding it changed exact +48h AP/AUC/Brier from 0.738/0.854/0.140 to 0.732/0.846/0.144, and any-hour AP/AUC/Brier from 0.766/0.812/0.171 to 0.774/0.806/0.175. At the locked cutoffs, exact alerts caught 77 vs 78 positives and produced 73 vs 64 false alarms; any-hour alerts caught 88 vs 87 and produced 59 vs 53 false alarms. The 2024–25 validation scores and false-alarm counts also worsened with inclusion. The results are mixed and do not justify changing the already evaluated primary model; report the sensitivity and keep the official source values available for future analysis.

On the 2025–26 holdout, only 28 eligible 4 PM forecast days remained after excluding starting AQI at or above 301. The primary exact +48-hour label had 19 positive forecast days. At the locked cutoff, the model caught 12/19 positive days with 5 false alarms; the AQI ≥250 reference caught 13/19 with 6 false alarms. This does **not** show an advantage over the simple reference for the primary outcome. The secondary any-hour model caught 16/23 positive days with 2 false alarms; the reference caught 15/23 with 4 false alarms. For unique onsets, only 11 had a usable test forecast window: the exact cutoff warned before 8 and the any-hour cutoff before 9. These small counts make the one-day differences unstable. The 24- and 72-hour outcomes are exploratory and have no locked alert cutoffs.

This is a small, unusually high-AQI holdout. Although the winter has 118 4 PM rows overall, only 28 are eligible for these onset-oriented models; 23/28 are positive for the secondary any-hour +48h label. Its AP of 0.93 is only modestly above the 0.82 prevalence reference, and its ROC AUC is 0.70 with a day-resampling range of 0.44–0.91. The exact +48h test AUC is 0.60 (range 0.34–0.82). Day-resampling ranges are rough because adjacent days are correlated. The week-block ranges apply to development folds and condition on the observed winters; they do not quantify uncertainty across the population of possible winters. These scores do not establish reliable operational alerts.

## Interpretation and next step

The development results suggest useful ranking, but the primary exact-endpoint result does not outperform the simple AQI threshold on the small holdout. The secondary any-hour result is slightly better on the locked alert counts, but the difference is only one positive forecast day and two false alarms. The historical 80% cutoff rule was based on **positive forecast days**, not unique events: the expanded six-winter any-hour table captures 77% of positive forecast days at the locked cutoff. Separately, on the 2025–26 test winter, that cutoff warned before 9 of 11 onsets with usable windows. Do not describe these as a robust event-capture rate.

Next, write the paper around the originally designated exact +48h crossing, report the 2025–26 result as-is, and treat the other five target/horizon combinations as secondary. Include all denominators, the baseline comparison, uncertainty limits, 2026 coverage, and the fact that many test forecasts start near the threshold. Predictor reporting latency at 4 PM has not been validated, so describe these as retrospective forecasts using observed inputs, not as a deployed warning service. Any further model or cutoff tuning needs a new future winter or an external holdout, not this test winter.

## Secondary exit, decision-value, and rainfall analyses

### Clearance from AQI 301 or above

The post-hoc exit task uses the same compact logistic-regression specification and predicts whether AQI is below 301 exactly 48 hours after a 4 PM start at AQI 301 or above. In six development winters, there were 412 eligible days and 105 clearances (reference AP 0.25). Leave-one-winter-out scores were AP/AUC/Brier 0.36/0.64/0.182 for AQI only, 0.44/0.69/0.173 for AQI plus season day, 0.53/0.74/0.160 for the compact model, and 0.55/0.75/0.160 for all columns. The compact model is numerically close to the all-column model; no paired uncertainty test establishes equivalence.

In winter 2025–26, 90 eligible days included 20 clearances. The compact model scored AUC 0.80 (day-resampling range 0.69–0.90), AP 0.57 (reference 0.22), and Brier 0.133. Mean predicted risk was 0.24 and the observed rate was 0.22. This close aggregate rate and the Brier score are encouraging, but they do not by themselves establish calibration across risk levels. The range resamples days, not weeks or winters, so it does not account fully for temporal dependence. Further, this exit analysis was formulated after the onset results and after the full-period rainfall diagnostic included 2025–26. Treat the exit test as exploratory evidence, not a pre-specified confirmatory test; a later winter is needed for prospective confirmation.

### Relative economic value

`results/rev_curves.png` and `results/rev_table.csv` summarize relative economic value (REV) from the development cross-winter predictions. Positive REV means better than taking no protective action; zero is the no-forecast reference. For the locked cutoff, REV for the exact +48h label was 0.38 at cost/loss ratio (alpha) 0.2, 0.45 at 0.3, and -0.04 at 0.5. For the any-hour label it was 0.09, 0.33, and 0.13 at those alpha values. The AQI ≥250 reference scored 0.24, 0.37, and -0.08 for exact, and -0.06, 0.25, and 0.12 for any-hour. Thus these development curves suggest value at some cost/loss trade-offs, not a universal benefit. The “best cutoff for each alpha” curve selects and scores the cutoff on the same predictions and is optimistic; it is exploratory. User-specific action thresholds would also require calibration and an explicit cost/loss choice.

### Rainfall diagnostic and oracle

The rainfall diagnostic sums observed station-average RF over the 48 hours after the 4 PM origin. It has 840 usable days from winter-start years 2018, 2019, and 2021–2025 (through winter 2025–26); rain was nonzero on 133/840 days (15.8%), while at least 1 mm occurred on 38/840 (4.5%). Among days starting at AQI 301 or above, the below-301 share at +48h was 19% with no rain, 50% with under 1 mm (52 days), 79% with 1–5 mm (14 days), and 80% above 5 mm (5 days). These are descriptive associations with small rainy-day groups and do not isolate rainfall from weather-system changes.

The oracle experiment includes **realized next-48-hour rain**, which is unavailable at forecast time. In leave-one-winter-out development evaluation, adding this future rain changed onset exact AP/AUC from 0.74/0.85 to 0.73/0.85 and onset any-hour from 0.77/0.81 to 0.76/0.81. For the exit task, AP/AUC/Brier changed from 0.53/0.74/0.160 to 0.62/0.80/0.145, and worst-winter AUC from 0.60 to 0.66. This suggests realized future rainfall carries additional signal for clearance in this dataset. It does **not** measure the value of a real rainfall forecast; that would require forecast rainfall inputs and a separate evaluation. Do not phrase the oracle as evidence that rainfall forecasts will deliver the same gain.

### Frozen model artifacts and prospective evaluation

`models/frozen_models.joblib` and its JSON metadata contain final refits trained on winters 2018–19 and 2021–26, including the 2025–26 holdout. These artifacts are for later use after the retrospective evaluation; they must not be used to reproduce the 2025–26 test metrics. The onset cutoffs are 0.3 (exact +48h) and 0.4 (any-hour +48h). The clearance model has no locked alert cutoff. For a prospective 2026–27 evaluation, freeze the outcomes, model inputs, all thresholds, and baseline comparisons before examining that winter’s results. Until predictive inputs are available at the intended issue time, describe the model as a retrospective study using observed 4 PM measurements.

The PM-derived AQI is a proxy and is not substituted for official city AQI. The January–February 2021 discrepancy is unresolved; do not treat the PM-derived proxy as a replacement for official AQI without a reproducible calculation and CPCB bulletin spot checks; see [2021 source notes](aqi_target/2021/README.md). When discussing the GRAP context, do not treat this project as a test of the full GRAP decision rule. See the [CAQM annual comparison](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1888090&lang=2&reg=48).

Run notebooks in order with the Jupyter working directory set to `notebooks/`. Relative paths use `../` to reach the repository folders. Install packages from `requirements.txt` and select that Python environment as the Jupyter kernel.

## Publication positioning

Delhi AQI and PM2.5 forecasting studies already exist, including daily AQI forecasting with recurrent models and multi-model PM2.5/AQI forecast evaluation. Treat these as examples for a full literature review, not an exhaustive list: [Pande et al. (2024)](https://www.sciencedirect.com/science/article/pii/S0269749124007541), [Yadav et al. (2025)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JD043719). Position this project around the fixed 4 PM threshold-crossing warning question, compact inputs, and winter-based evaluation; do not claim novelty as generic Delhi AQI machine learning.

For evaluation methods, discuss why time-ordered validation matters for dependent observations and cite [Roberts et al. (2017)](https://www.wsl.ch/lud/biodiversity_events/papers/Roberts_et_al-2017-Ecography.pdf). For probability quality, explain Brier score/skill alongside discrimination and refer to [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf). These are starting references; verify citation details and expand the literature review before submission.

The current rainfall diagnostic includes winter 2025–26 and has 840 usable rows, while an earlier summary listed 781. Reconcile that denominator before publication. Any rainfall-informed model selection needs a later untouched winter or external evaluation.
