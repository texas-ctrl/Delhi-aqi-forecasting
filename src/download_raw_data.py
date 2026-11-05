
import pandas as pd
from pathlib import Path

rows = []
for f in sorted(Path("raw_data").glob("*/*.csv")):
    d = pd.read_csv(f)
    pm = [c for c in d.columns if c.startswith("PM2.5")][0]
    rows.append((f.parent.name, f.name[9:13], len(d), round(d[pm].notna().mean() * 100)))
print(pd.DataFrame(rows, columns=["station", "year", "rows", "pm25_present_%"]).to_string(index=False))