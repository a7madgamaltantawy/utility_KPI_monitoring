import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

st.title("⚡ Utility KPI Monitoring Dashboard")

companies = requests.get(f"{API_URL}/companies").json()
company_names = [c["company_name"] for c in companies]

selected_company = st.sidebar.selectbox("Company", company_names)

kpis = requests.get(f"{API_URL}/kpis/{selected_company}").json()
df = pd.DataFrame(kpis)

benchmark = pd.DataFrame(requests.get(f"{API_URL}/benchmark").json())

st.metric("SAIDI YTD", round(df["saidi_hours_per_customer"].sum(), 2))
st.metric("Avg SAIFI", round(df["saifi_interruptions_per_customer"].mean(), 3))
st.metric("Avg Loss %", round(df["total_loss_pct"].mean(), 2))

fig = px.line(
    df,
    x="month",
    y=["saidi_hours_per_customer", "total_loss_pct"],
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Benchmark")
st.dataframe(benchmark)