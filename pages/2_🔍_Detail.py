import streamlit as st
import pandas as pd
from data.bq_client import query_data, DATASET

st.title("Data dari BigQuery")

# Ambil nama dataset dari secrets.toml

# Gunakan f-string agar stabil
sql_query = f"""
    SELECT * 
    FROM `{DATASET}.POTS_JOINED`
    LIMIT 100
"""
# Tarik data dari BigQuery. Fungsi ini sudah memiliki @st.cache_data
# Sehingga query tidak akan dijalankan berulang kali setiap ada interaksi UI (menghemat biaya).
try:
    df = query_data(sql_query)
    
    # Tampilkan dataframe di Streamlit
    st.dataframe(df)
except Exception as e:
    st.error(f"Gagal mengambil data dari BigQuery: {e}")