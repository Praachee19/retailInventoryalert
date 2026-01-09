import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Retail Performance & Inventory Dashboard", layout="wide")

st.title("Retail Sales & Inventory Dashboard")
st.caption("Explainable AI driven insights from national to SKU level")

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload your retail dataset CSV file", type=["csv"])

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)
    df["Date"] = pd.to_datetime(df["Date"])

    # -----------------------------
    # Inventory Simulation Logic (EXPLAINABLE)
    # -----------------------------
    if "Inventory_Level" not in df.columns:
        df["Inventory_Level"] = (df["Quantity"] * 10).astype(int)
        df["Reorder_Level"] = 100

    def alert_logic(row):
        if row["Inventory_Level"] > row["Reorder_Level"]:
            return "Green", "Stock is healthy. No action required."
        elif row["Inventory_Level"] == row["Reorder_Level"]:
            return "Orange", "Stock at reorder point. Plan replenishment."
        else:
            return "Red", "Stock below reorder point. Immediate action needed."

    df[["Alert_Color", "Alert_Reason"]] = df.apply(
        lambda r: pd.Series(alert_logic(r)), axis=1
    )

    def recommended_action(color):
        if color == "Red":
            return "Reorder immediately or transfer stock"
        elif color == "Orange":
            return "Monitor sales velocity and reorder soon"
        else:
            return "No action required"

    df["Recommended_Action"] = df["Alert_Color"].apply(recommended_action)

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("Filters")
    filtered_df = df.copy()

    for col in ["Region", "State", "Sub_Category", "Product_Name", "SKU"]:
        options = ["All"] + sorted(filtered_df[col].dropna().unique().tolist())
        selection = st.sidebar.selectbox(col.replace("_", " "), options)
        if selection != "All":
            filtered_df = filtered_df[filtered_df[col] == selection]

    # -----------------------------
    # KPIs
    # -----------------------------
    total_sales = filtered_df["Sales"].sum()
    total_profit = filtered_df["Profit"].sum()
    total_stores = filtered_df["Store_Code"].nunique()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Sales", f"${total_sales:,.0f}")
    kpi2.metric("Total Profit", f"${total_profit:,.0f}")
    kpi3.metric("Active Stores", total_stores)

    # -----------------------------
    # EXPLAINABLE AI PANEL
    # -----------------------------
    st.markdown("### 🧠 AI Explanation Panel")

    st.info(
        f"""
**Why these numbers matter**

• **Total Sales** reflect demand across selected filters.  
• **Total Profit** shows pricing and discount efficiency.  
• **Active Stores** indicate distribution reach.

⚠️ If profit grows slower than sales, discounting or cost leakage may exist.
        """
    )

    # -----------------------------
    # Charts
    # -----------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "Sales by Region",
        "Category Breakdown",
        "Monthly Trend",
        "Inventory Alerts (Explainable)"
    ])

    with tab1:
        region_sales = filtered_df.groupby("Region", as_index=False)["Sales"].sum()
        fig1 = px.bar(region_sales, x="Region", y="Sales", title="Sales by Region")
        st.plotly_chart(fig1, use_container_width=True)

        st.caption("Explanation: Regions with lower sales may need assortment or pricing review.")

    with tab2:
        category_sales = filtered_df.groupby("Sub_Category", as_index=False)["Sales"].sum()
        fig2 = px.pie(category_sales, names="Sub_Category", values="Sales")
        st.plotly_chart(fig2, use_container_width=True)

        st.caption("Explanation: Categories driving sales deserve higher space and inventory priority.")

    with tab3:
        monthly_sales = (
            filtered_df
            .groupby(filtered_df["Date"].dt.to_period("M"))["Sales"]
            .sum()
            .reset_index()
        )
        monthly_sales["Date"] = monthly_sales["Date"].astype(str)
        fig3 = px.line(monthly_sales, x="Date", y="Sales", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

        st.caption("Explanation: Drops may indicate seasonality, stockouts, or pricing issues.")

    with tab4:
        alert_view = filtered_df[
            ["Store_Code", "Product_Name", "SKU", "Inventory_Level",
             "Reorder_Level", "Alert_Color", "Alert_Reason", "Recommended_Action"]
        ]

        st.dataframe(alert_view, use_container_width=True)

        st.caption(
            """
**Alert Logic Explained**

• Green → Inventory safely above reorder level  
• Orange → Inventory touching reorder point  
• Red → Inventory below reorder level, risk of lost sales  

Each alert includes *why* it triggered and *what to do next*.
            """
        )

        alert_counts = filtered_df["Alert_Color"].value_counts().reset_index()
        alert_counts.columns = ["Alert_Color", "Count"]

        fig4 = px.bar(alert_counts, x="Alert_Color", y="Count", color="Alert_Color",
                      title="Inventory Risk Distribution")
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Upload a CSV file to activate the Explainable AI dashboard.")
