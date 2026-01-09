# retail_pipeline.py
# Generates a 5,000 row retail dataset with your exact columns.
# Computes reorder alerts. Saves Excel and CSV. Optional. emails alerts. pushes alerts to Google Sheets.

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Optional email
import smtplib
from email.mime.text import MIMEText

# Optional Google Sheets
# pip install gspread google-auth
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSHEETS = True
except Exception:
    HAS_GSHEETS = False

# ---------------------
# Paths and constants
# ---------------------
ROOT = os.getcwd()
OUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUT_DIR, exist_ok=True)

DATA_CSV = os.path.join(OUT_DIR, "retail_dataset.csv")
DATA_XLSX = os.path.join(OUT_DIR, "retail_dataset.xlsx")
ALERT_LATEST = os.path.join(OUT_DIR, "low_stock_alert_latest.csv")

# ---------------------
# Data generation
# ---------------------
def generate_dataset(n_rows=5000, seed=42, start_date="2025-01-01", months=6):
    random.seed(seed)
    np.random.seed(seed)

    countries = ["India"]
    regions = ["North", "West", "South", "East", "Central"]
    states_by_region = {
        "North": ["Delhi", "Haryana", "Uttar Pradesh", "Rajasthan"],
        "West": ["Maharashtra", "Gujarat"],
        "South": ["Karnataka", "Tamil Nadu", "Telangana"],
        "East": ["West Bengal", "Odisha"],
        "Central": ["Madhya Pradesh", "Chhattisgarh"]
    }
    cities_by_state = {
        "Delhi": ["New Delhi", "Delhi"],
        "Haryana": ["Gurgaon", "Faridabad"],
        "Uttar Pradesh": ["Noida", "Lucknow"],
        "Rajasthan": ["Jaipur", "Udaipur"],

        "Maharashtra": ["Mumbai", "Pune", "Nashik"],
        "Gujarat": ["Ahmedabad", "Surat"],

        "Karnataka": ["Bangalore", "Mysore"],
        "Tamil Nadu": ["Chennai", "Coimbatore"],
        "Telangana": ["Hyderabad", "Warangal"],

        "West Bengal": ["Kolkata", "Howrah"],
        "Odisha": ["Bhubaneswar", "Cuttack"],

        "Madhya Pradesh": ["Indore", "Bhopal"],
        "Chhattisgarh": ["Raipur", "Bilaspur"]
    }
    # simple areas per city
    areas = ["Central", "East", "West", "North", "South", "Market", "Mall", "HighStreet", "Industrial", "Residential"]

    store_footprints = [600, 800, 1000, 1200, 1500, 1800, 2000]
    categories = ["Apparel", "Electronics", "Beverages", "Home", "Beauty"]
    sub_categories = {
        "Apparel": ["Menswear", "Womenswear", "Kidswear"],
        "Electronics": ["Smartphones", "Laptops", "Accessories"],
        "Beverages": ["Soft Drinks", "Juices", "Water"],
        "Home": ["Kitchen", "Bedding", "Storage"],
        "Beauty": ["Skincare", "Haircare", "Fragrance"]
    }
    brands_map = {
        "Menswear": ["Adidas", "Nike", "Zara"],
        "Womenswear": ["Zara", "H&M", "Biba"],
        "Kidswear": ["Zara", "AllenSolly", "GiniJony"],
        "Smartphones": ["Samsung", "Apple", "Xiaomi", "OnePlus"],
        "Laptops": ["HP", "Lenovo", "Dell", "Apple"],
        "Accessories": ["Boat", "Sony", "JBL", "Mi"],
        "Soft Drinks": ["Coke", "Pepsi", "ThumsUp"],
        "Juices": ["Tropicana", "Real", "PaperBoat"],
        "Water": ["Bisleri", "Kinley", "Aquafina"],
        "Kitchen": ["Prestige", "Pigeon", "Butterfly"],
        "Bedding": ["Spaces", "Portico", "DDecor"],
        "Storage": ["Tupperware", "Cello", "Milton"],
        "Skincare": ["Lakme", "LOreal", "Nivea"],
        "Haircare": ["Tresemme", "Sunsilk", "Head&Shoulders"],
        "Fragrance": ["CalvinKlein", "Davidoff", "Skinn"]
    }

    start = datetime.fromisoformat(start_date)
    end_days = months * 30

    rows = []
    for i in range(n_rows):
        region = random.choice(regions)
        state = random.choice(states_by_region[region])
        city = random.choice(cities_by_state[state])
        area = random.choice(areas)
        store_area = int(random.choice(store_footprints))
        store_code = f"{city[:3].upper()}_{area[:3].upper()}_{np.random.randint(1, 500):04d}"

        cat = random.choice(categories)
        sub = random.choice(sub_categories[cat])
        brand = random.choice(brands_map[sub])
        sku_num = np.random.randint(10000, 99999)
        sku = f"SKU{sku_num}"
        product_name = f"{brand} {sub} {np.random.randint(1, 999)}"

        # pricing and quantity
        unit_price = float(random.choice([99, 149, 199, 249, 499, 799, 999, 1299, 1999, 4999, 9999, 14999]))
        # distribution for quantity
        q_base = max(0, np.random.poisson(lam=4) + np.random.randint(0, 5))
        if cat in ["Electronics"]:
            q_base = max(1, int(q_base * 0.6))
        quantity = int(q_base)

        sales = round(unit_price * quantity * np.random.uniform(0.95, 1.05), 2)
        margin = {"Apparel": 0.45, "Electronics": 0.18, "Beverages": 0.30, "Home": 0.35, "Beauty": 0.40}.get(cat, 0.30)
        profit = round(sales * margin * np.random.uniform(0.9, 1.1), 2)
        sales_per_sqft = round(sales / store_area, 4)

        # inventory for alerting
        reorder_point = int(random.choice([10, 15, 20, 25, 30]))
        stock_qty = int(max(0, np.random.normal(loc=25, scale=10)))
        # inject low stock
        if np.random.rand() < 0.18:
            stock_qty = int(np.random.randint(0, reorder_point))

        # date
        date = start + timedelta(days=int(np.random.randint(0, end_days)))

        rows.append([
            "India", region, state, city, area, store_code, store_area, sales_per_sqft,
            cat, sub, product_name, sku, unit_price, quantity, sales, profit,
            stock_qty, reorder_point, date.date().isoformat()
        ])

    df = pd.DataFrame(rows, columns=[
        "country", "region", "state", "city", "area", "store_code", "store_area", "sales_per_sqft",
        "category", "sub_category", "product_name", "sku", "unit_price", "quantity", "sales", "profit",
        "stock_qty", "reorder_point", "date"
    ])

    df.to_csv(DATA_CSV, index=False)
    df.to_excel(DATA_XLSX, index=False, sheet_name="Sheet2")
    return df

# ---------------------
# Alerts
# ---------------------
def low_stock_alerts(df: pd.DataFrame) -> pd.DataFrame:
    low = df[df["stock_qty"] <= df["reorder_point"]].copy()
    low = low.sort_values(["stock_qty", "reorder_point", "sku"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    low.to_csv(ALERT_LATEST, index=False)
    versioned = os.path.join(OUT_DIR, f"low_stock_alert_{ts}.csv")
    low.to_csv(versioned, index=False)
    return low

# ---------------------
# Email
# ---------------------
def send_email_alert(df_alert: pd.DataFrame,
                     to_email: str,
                     sender_email: str,
                     sender_app_password: str,
                     smtp_host="smtp.gmail.com", smtp_port=587):
    if not to_email or not sender_email or not sender_app_password:
        print("Email not sent. configure to_email, sender_email, sender_app_password.")
        return False

    if df_alert.empty:
        subject = "Stock health OK"
        body = "<p>All SKUs are above reorder levels.</p>"
    else:
        subject = f"Reorder alert. {len(df_alert)} SKUs at or below reorder"
        body = f"""
        <h3>Reorder Alert</h3>
        <p>The following SKUs are at or below reorder level.</p>
        {df_alert.head(150).to_html(index=False)}
        <p>Full CSV is saved on the server.</p>
        """

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_app_password)
        server.send_message(msg)
    print("Email sent")
    return True

# ---------------------
# Google Sheets
# ---------------------
def push_alerts_to_google_sheet(df_alert: pd.DataFrame,
                                spreadsheet_name: str,
                                worksheet_name: str,
                                service_account_json: str):
    if not HAS_GSHEETS:
        print("gspread or google-auth missing. run pip install gspread google-auth")
        return False
    if not os.path.exists(service_account_json):
        print("service account JSON not found.")
        return False

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(service_account_json, scopes=scopes)
    gc = gspread.authorize(creds)

    try:
        sh = gc.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(spreadsheet_name)

    try:
        ws = sh.worksheet(worksheet_name)
        sh.del_worksheet(ws)
    except Exception:
        pass
    ws = sh.add_worksheet(title=worksheet_name, rows=str(max(1000, len(df_alert)+10)), cols="26")

    values = [list(df_alert.columns)] + df_alert.astype(str).values.tolist()
    ws.update("A1", values)
    print(f"Pushed {len(df_alert)} rows to Google Sheet. {spreadsheet_name} . {worksheet_name}")
    return True

# ---------------------
# Main
# ---------------------
if __name__ == "__main__":
    # 1. generate 5k rows
    df = generate_dataset(n_rows=5000)
    print(f"Generated dataset. rows. {len(df)}")
    print(f"Wrote. {DATA_CSV}")
    print(f"Wrote. {DATA_XLSX}")

    # 2. alerts
    alerts = low_stock_alerts(df)
    print(f"Low stock rows. {len(alerts)}")
    print(f"Latest alert CSV. {ALERT_LATEST}")

    # 3. optional email
    # send_email_alert(
    #     df_alert=alerts,
    #     to_email="supplychain@yourcompany.com",
    #     sender_email="retail.alerts@yourdomain.com",
    #     sender_app_password="your_app_password_here"
    # )

    # 4. optional Google Sheets
    # push_alerts_to_google_sheet(
    #     df_alert=alerts,
    #     spreadsheet_name="Retail_Reorder_Alerts",
    #     worksheet_name="Alerts",
    #     service_account_json=r"C:\path\to\service_account.json"
    # )

    print("Done.")