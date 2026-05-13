import streamlit as st
import pandas as pd
from components.charts import render_bar_chart
from components.metrics import render_kpi_card

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

st.title("📊 Overview")

st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card("Total Revenue", "Rp 150.000.000", "+5% dari bulan lalu")
with col2:
    render_kpi_card("Total Pelanggan", "1,250", "+12 dari bulan lalu")
with col3:
    render_kpi_card("Active Issues", "5", "-2 dari bulan lalu")

st.markdown("---")

st.subheader("Trend Penjualan (Contoh ECharts)")
categories = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
values = [120, 200, 150, 80, 70, 110]

render_bar_chart(categories, values, title="Penjualan 2026")
