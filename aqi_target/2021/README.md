Corrected 2021 hourly AQI source

The file delhi_2021_hourly_station_mean.csv is built from 39 CPCB-sourced Delhi station AQI files stored in cpcb_station_source_2017_2023/. Each timestamp is the mean of available reporting-station AQI values. The Stations_reporting field records how many station readings were used. There are 8,741 observed hours out of 8,760; 19 hours have no station reading and remain blank.

The original 2021 city-level monthly Excel files remain in this folder for reference and are not used by the updated notebook. Their monthly averages disagreed substantially with CAQM.

Source catalog: https://data.opencity.in/dataset/delhi-hourly-air-quality-reports (source metadata: airquality.cpcb.gov.in)
Method: https://aqi.delhi.gov.in/faq
CAQM 2021 figures: https://www.pib.gov.in/PressReleasePage.aspx?PRID=1991970&lang=2&reg=3 (the later 2023 table reports May 2021 as 144)
