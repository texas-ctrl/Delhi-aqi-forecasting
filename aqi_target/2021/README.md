2021 AQI source notes

The project keeps the original hourly city-level CPCB workbook values unchanged. Notebook 01 adds an `AQI_review_status` column; it does not rewrite source values.

A comparison of AQI derived from six-station PM data reports strong daily agreement with the city workbook in October–December 2021 (correlations 0.99, 0.93, and 0.95) and weak agreement in January–September. On 20 August at 4 PM, the PM-derived AQI is reported as 119, the CPCB bulletin is 111, and the workbook is 256. On 20 December, the workbook and bulletin both report 332. These checks support flagging January–September, but the PM-derived AQI is a proxy; its calculation should be saved and spot-checked against additional CPCB bulletins before it is used to repair any target values.

Notebook 02 masks January–September AQI values in its analysis copy while leaving pollutant/weather observations and the original processed source CSV intact. It excludes winter 2020 (November 2020–February 2021) from the primary winter analysis, but retains winter 2021–22 because November–December 2021 are cross-check consistent and January–February 2022 use the regular city-level source.

CPCB bulletins:
- 20 August 2021: https://cpcb.nic.in/displaypdf.php?id=RG93bmxvYWRzL0FRSV9CdWxsZXRpbl8yMDIxMDgyMC5wZGY%3D
- 20 December 2021: https://cpcb.nic.in/displaypdf.php?id=RG93bmxvYWRzL0FRSV9CdWxsZXRpbl8yMDIxMTIyMC5wZGY%3D

CAQM annual/monthly comparison: https://www.pib.gov.in/PressReleasePage.aspx?PRID=1991970&lang=2&reg=3
