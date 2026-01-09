# app_utils.py
import os
import pandas as pd

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
DATA_CSV = os.path.join(OUTPUT_DIR, "retail_dataset.csv")
ALERT_LATEST = os.path.join(OUTPUT_DIR, "low_stock_alert_latest.csv")

def _ensure_cols(df, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

def load_dataset():
    if not os.path.exists(DATA_CSV):
        raise FileNotFoundError(f"{DATA_CSV} not found. Run retail_pipeline.py")
    df = pd.read_csv(DATA_CSV)
    _ensure_cols(df, [
        "country","region","state","city","area","store_code","store_area",
        "sales_per_sqft","category","sub_category","product_name","sku",
        "unit_price","quantity","sales","profit","stock_qty","reorder_point","date"
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["month_start"] = df["date"].values.astype("datetime64[M]")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df

def load_alerts():
    if not os.path.exists(ALERT_LATEST):
        return pd.DataFrame()
    df = pd.read_csv(ALERT_LATEST)
    # align types if needed
    for c in ["region","state","city","area","store_code","category","sub_category","sku"]:
        if c in df.columns:
            df[c] = df[c].astype(str)
    return df

def filter_df(df, f):
    out = df.copy()
    for k, v in f.items():
        if v is None:
            continue
        if isinstance(v, list):
            if len(v) == 0:
                continue
            out = out[out[k].isin(v)]
        else:
            if v == "All":
                continue
            out = out[out[k] == v]
    return out

def mom_change(series_by_month):
    # expects a DataFrame with columns ["month_start","value"]
    s = series_by_month.sort_values("month_start").reset_index(drop=True)
    if len(s) < 2:
        return None
    last = s.iloc[-1]["value"]
    prev = s.iloc[-2]["value"]
    if prev == 0:
        return None
    return (last - prev) / prev

def yoy_change(series_by_month):
    # compare last month to same month last year if present
    s = series_by_month.sort_values("month_start")
    if len(s) < 13:
        return None
    last = s.iloc[-1]
    same_month_last_year = s[s["month_start"] == (last["month_start"] - pd.DateOffset(years=1))]
    if same_month_last_year.empty:
        return None
    prev = same_month_last_year.iloc[-1]["value"]
    if prev == 0:
        return None
    return (last["value"] - prev) / prev
