import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
from utils.data_processing import get_filter_options, get_pivoted_data_from_bq, get_layanan_pivoted_data_from_bq, get_top_bottom_pelanggan_from_bq
from utils.helpers import setup_page, highlight_totals

setup_page(title="PRQ Dashboard | Detail")

st.title("CBASE SME")

FILTER_CONTAINER_HEIGHT = 750
CONTENT_CONTAINER_HEIGHT = 690

def main():
    try:
        filter_opts = get_filter_options()
        
        col_filter, col_content = st.columns([1, 4])
        
        with col_filter:
            with st.container(height=FILTER_CONTAINER_HEIGHT):
                st.subheader("Filter Data")
                
                filters = {}
                filters["years"] = st.multiselect("Tahun", options=filter_opts["years"], default=[2026])
                filters["flags"] = st.multiselect("FLAG REVENUE", options=filter_opts["flags"], default=[])
                filters["subsegmen"] = st.multiselect("SUBSEGMEN HO", options=filter_opts["subsegmen"], default=[])
                filters["bam"] = st.multiselect("NAMA BAM", options=filter_opts["bam"], default=[])
                filters["telda"] = st.multiselect("TELDA", options=filter_opts["telda"], default=[])
                filters["sto"] = st.multiselect("STO", options=filter_opts["sto"], default=[])
                filters["nipnas_search"] = st.text_input("Cari NO NIPNAS", value="")
                
        with col_content:
            tab_chart, tab_layanan, tab_pelanggan = st.tabs(["Overview", "Layanan", "Rank Pelanggan"])
            
            with tab_chart:            
                render_overview_tab(filters)
                
            with tab_layanan:
                render_layanan_tab(filters)
                
            with tab_pelanggan:
                render_pelanggan_tab(filters)
    except Exception as e:
        st.error(f"Gagal mengambil data dari BigQuery: {e}")

def render_overview_tab(filters):
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        result = get_pivoted_data_from_bq(filters)
        
        if result[0] is not None:
            pivot_df, x_axis_data, series_data = result

            options = {
                "title": {"text": "Trend Total Revenue"},
                "tooltip": {"trigger": "axis"},
                "legend": {
                    "data": ["Total Revenue"],
                    "top": "bottom"
                },
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
                "toolbox": {
                    "feature": {
                        "saveAsImage": {}
                    }
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": x_axis_data
                },
                "yAxis": {
                    "type": "value"
                },
                "series": series_data
            }

            st.subheader("Trend Total Revenue")
            st_echarts(options=options, height="350px")
            
            st.subheader("Tabel Revenue")
            
            st.dataframe(
                pivot_df.style.apply(highlight_totals, axis=None).format(thousands=".", precision=0), 
                width="stretch"
            )

        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")

def render_layanan_tab(filters):
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        st.subheader("Tabel Revenue per Layanan")
        
        pivot_df = get_layanan_pivoted_data_from_bq(filters)
        
        if pivot_df is not None:
            st.dataframe(
                pivot_df.style.apply(highlight_totals, axis=None).format(thousands=".", precision=0), 
                width="stretch"
            )
        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")

def render_pelanggan_tab(filters):
    with st.container(height=CONTENT_CONTAINER_HEIGHT):
        st.subheader("Rank 10 Pelanggan")
        
        top_df, bottom_df = get_top_bottom_pelanggan_from_bq(filters, n=10)
        
        if top_df is not None and bottom_df is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top 10 Pelanggan**")
                st.dataframe(
                    top_df.style.format(thousands=".", precision=0), 
                    width="stretch"
                )
                
            with col2:
                st.markdown("**Bottom 10 Pelanggan**")
                st.dataframe(
                    bottom_df.style.format(thousands=".", precision=0), 
                    width="stretch"
                )
        else:
            st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")

if __name__ == "__main__":
    main()
