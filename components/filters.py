import streamlit as st

AVAILABLE_YEARS = ["2026", "2025", "2024"]
AVAILABLE_WITELS = ["JTB", "Lainnya"]

def render_sidebar_filters() -> dict[str, str]:
    """
    Render common filters in the sidebar.
    Returns a dictionary of selected filters.
    """
    st.sidebar.header("🛠️ Filter Data")
    
    selected_year = st.sidebar.selectbox("Pilih Tahun", AVAILABLE_YEARS)
    selected_witel = st.sidebar.selectbox("Pilih Witel", AVAILABLE_WITELS)
    
    return {
        "year": selected_year,
        "witel": selected_witel
    }
