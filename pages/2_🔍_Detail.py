import streamlit as st
from streamlit_echarts import st_echarts
from utils.data_processing import get_filter_options, get_pivoted_data_from_bq

st.set_page_config(
    page_title="PRQ Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Data dari BigQuery")

try:
    available_years, available_flags = get_filter_options()
    
    col_filter, col_content = st.columns([1, 3])
    
    with col_filter:
        with st.container(height=700):
            st.subheader("Filter Data")
            
            selected_years = st.multiselect("Tahun", options=available_years, default=[])
            selected_flags = st.multiselect("FLAG REVENUE", options=available_flags, default=[])
            
    with col_content:
        with st.container(height=700):
            
            result = get_pivoted_data_from_bq(selected_years, selected_flags)
            
            if result[0] is not None:
                pivot_df, x_axis_data, series_data = result
                
                st.subheader("Pivot Table Revenue")
                st.dataframe(pivot_df, use_container_width=True)

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

                st.subheader("Line Chart Trend Total Revenue")
                st_echarts(options=options, height="500px")
            else:
                st.warning("Data kosong. Tidak ada data yang sesuai dengan filter yang dipilih.")
                
except Exception as e:
    st.error(f"Gagal mengambil data dari BigQuery: {e}")