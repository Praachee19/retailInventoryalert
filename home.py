# Home.py
import streamlit as st
from app_utils import load_dataset
import joblib
st.set_page_config(page_title="Retail Analytics Suite", layout="wide")

st.title("Retail Analytics Suite")
st.caption("Sales. Profitability. Live Alerts. Auto-refreshed from the pipeline outputs.")

try:
    df = load_dataset()
    st.success("Dataset loaded")
    st.write("Rows:", len(df))
    st.write("Date range:", df["date"].min().date(), "to", df["date"].max().date())
    st.write("Dimensions. Country, Region, State, City, Area, Store, Category, Sub Category, SKU")
    st.write("Metrics. Sales, Profit, Quantity, Sales per Sq Ft")
except Exception as e:
    st.error(str(e))
    st.info("Run. python retail_pipeline.py")

    model = joblib.load('Home_Model.pkl')
joblib.dump(model,'Home_Model.pkl')