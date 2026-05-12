import streamlit as st

def render_sidebar_filters():
    """
    Render common filters in the sidebar.
    Returns a dictionary of selected filters.
    """
    st.sidebar.header("🛠️ Filter Data")
    
    selected_year = st.sidebar.selectbox("Pilih Tahun", ["2026", "2025", "2024"])
    selected_witel = st.sidebar.selectbox("Pilih Witel", ["JTB", "Lainnya"])
    
    return {
        "year": selected_year,
        "witel": selected_witel
    }
